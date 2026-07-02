"""Guided narrative intake — the agentic flow.

Step 2 builds the front of the pipeline:
  create_draft(): classify + ingest the kernel (URL -> ingest_url; text -> as-is),
                  persist a narrative_drafts row, and generate the first round of
                  questions via the LLM.
  propose_questions(): the GLM structured call that turns a kernel (+ any prior
                  answers) into adaptive, POSITION-SEEKING questions.

Synthesis and the answer loop come in later steps.
"""

from collections import defaultdict
from uuid import UUID

from pydantic import BaseModel
from supabase import Client

from app.models import (
    CompanyAttach,
    IngestResult,
    IntakeAnswerRequest,
    IntakeState,
    Kernel,
    KernelKind,
    KernelSummary,
    NarrativeCreate,
    Proposal,
    Question,
)
from app.providers import llm
from app.providers.ingest import ingest_url
from app.services import companies as companies_service
from app.services import narratives as narratives_service

MAX_ROUNDS = 3  # question rounds before we synthesize regardless


class KernelIngestError(Exception):
    """A URL kernel couldn't be turned into usable content (-> error state)."""

    def __init__(self, result: IngestResult):
        self.result = result
        super().__init__(result.reason.value if result.reason else "ingest_failed")


class QuestionSet(BaseModel):
    """LLM output for question generation."""

    ready: bool
    rationale: str = ""
    questions: list[Question] = []


_QUESTIONS_SYSTEM = """\
You are Tamara, an investment-research assistant. You turn a rough KERNEL (the
content of a link, a tweet, or a note) into a SHARP, COMMITTED investment thesis
that takes a position.

Right now, decide whether you have enough to draft a useful, *positioned*
narrative. If yes, set ready=true and return no questions. If not, ask up to 4
sharp, NON-REDUNDANT questions that pin down or establish the POSITION — only
what is missing.

Principles:
- Push toward a position. Infer the implied directional stance (long/short, the
  bet) from the kernel and aim questions at sharpening that bet — never produce a
  neutral, both-sides survey. If the kernel is directionless, ask what side the
  user wants to take.
- Target only the gaps among: the specific claim/direction, which companies or
  tickers, time horizon, the strongest bull point, what would break it
  (bear/risk), dated catalysts, the user's edge / why now. Never ask what the
  kernel already answers.
- Each question: offer 2-4 concrete options (label + short description) and allow
  a free-text answer. Keep them tight and concrete.

Output JSON matching the schema. Each question needs: id (stable lowercase slug),
header (<= 16 chars), question, options (label + optional description),
multi_select, allow_free_text."""


def propose_questions(kind: KernelKind, content: str, transcript: list[dict]) -> QuestionSet:
    """Ask the model for the next round of position-seeking questions."""
    prior = ""
    if transcript:
        prior = "\n\nPRIOR Q&A:\n" + "\n".join(
            str(turn) for turn in transcript if "answers" in turn
        )
    messages = [
        {"role": "system", "content": _QUESTIONS_SYSTEM},
        {"role": "user", "content": f'KERNEL (kind={kind.value}):\n"""\n{content[:6000]}\n"""{prior}'},
    ]
    return llm.structured(messages, QuestionSet, role="fast")


def create_draft(db: Client, user_id: UUID, kernel: Kernel) -> IntakeState:
    """Start an intake: ingest the kernel, persist a draft, return round-1 questions."""
    title = excerpt = url = raw = None
    kind = kernel.kind

    if kernel.url:
        result = ingest_url(kernel.url)
        if not result.ok:
            raise KernelIngestError(result)
        kind = result.source_kind  # url or tweet
        url, title, excerpt = result.url, result.title, result.excerpt
        content = f"{title}\n\n{excerpt}" if title else excerpt
    else:
        raw = (kernel.raw_text or "").strip()
        if not raw:
            raise ValueError("empty kernel")
        kind, content = KernelKind.text, raw

    question_set = propose_questions(kind, content, transcript=[])
    questions = question_set.questions

    payload = {
        "user_id": str(user_id),
        "status": "collecting",
        "kernel_kind": kind.value,
        "kernel_raw": raw,
        "kernel_url": url,
        "kernel_title": title,
        "kernel_excerpt": excerpt,
        "round": 1,
        "transcript": [{"round": 1, "questions": [q.model_dump() for q in questions]}],
    }
    draft = db.table("narrative_drafts").insert(payload).execute().data[0]

    return IntakeState(
        draft_id=draft["id"],
        status=draft["status"],
        kernel=KernelSummary(kind=kind, title=title, excerpt=(excerpt or raw or "")[:300]),
        round=1,
        questions=questions,
    )


class DraftNotFound(Exception):
    """No draft with that id for the caller (RLS-scoped)."""


_SYNTH_SYSTEM = """\
You are Tamara. Synthesize the KERNEL and the user's answers into a SHARP,
COMMITTED investment narrative that takes a position.

Produce, matching the schema:
- title: a concise, assertive title that names the bet.
- thesis: 2-4 sentences stating the POSITION as a committed directional claim
  (the bet and why it works), in the user's framing. Take a side; do NOT hedge
  into a neutral both-sides summary.
- companies: the names the thesis is about — ticker + exchange (e.g. CEG /
  NASDAQ), using the user's choices and the kernel. NEVER invent a ticker; if
  unsure of the exact symbol or exchange, use the most likely and note the
  uncertainty in open_questions.
- items: the argument as bull/bear/catalyst/risk points. The BULL case is THE
  case (the position, foregrounded). bear and risk are the COUNTER — what would
  break the thesis — not equal-weight hedging. catalysts may carry event_date
  (ISO date). For each item set cite="kernel" ONLY if the kernel text supports
  it, else null. Do not fabricate facts, financials, or dates.
- confidence: low | medium | high — be honest.
- open_questions: genuinely open threads worth chasing."""


def synthesize_narrative(kind: KernelKind, content: str, transcript: list[dict]) -> Proposal:
    """Turn the kernel + answers into a committed, positioned draft narrative."""
    messages = [
        {"role": "system", "content": _SYNTH_SYSTEM},
        {
            "role": "user",
            "content": f'KERNEL (kind={kind.value}):\n"""\n{content[:6000]}\n"""\n\nQ&A:\n{_format_qa(transcript)}',
        },
    ]
    return llm.structured(messages, Proposal, role="synthesis")


def answer(db: Client, draft_id: UUID, req: IntakeAnswerRequest) -> IntakeState:
    """Record this round's answers, then either ask more questions or synthesize."""
    draft = _load_draft(db, draft_id)
    if draft["status"] != "collecting":
        return _state_from_draft(draft)  # already proposed/finalized — idempotent

    kind, content = _kernel_content(draft)
    transcript = list(draft["transcript"])
    current_round = draft["round"]
    transcript.append(
        {"round": current_round, "answers": [a.model_dump(mode="json") for a in req.answers]}
    )

    ready = req.finish_now or current_round >= MAX_ROUNDS
    next_questions: list[Question] | None = None
    if not ready:
        question_set = propose_questions(kind, content, transcript)
        if question_set.ready or not question_set.questions:
            ready = True
        else:
            current_round += 1
            next_questions = question_set.questions
            transcript.append(
                {"round": current_round, "questions": [q.model_dump(mode="json") for q in next_questions]}
            )

    summary = _kernel_summary(draft, kind)

    if ready:
        proposal = synthesize_narrative(kind, content, transcript)
        _update_draft(
            db,
            draft_id,
            {
                "transcript": transcript,
                "round": current_round,
                "status": "proposed",
                "proposal": proposal.model_dump(mode="json"),
            },
        )
        return IntakeState(
            draft_id=draft["id"], status="proposed", kernel=summary, round=current_round, proposal=proposal
        )

    _update_draft(db, draft_id, {"transcript": transcript, "round": current_round})
    return IntakeState(
        draft_id=draft["id"], status="collecting", kernel=summary, round=current_round, questions=next_questions
    )


def get_draft(db: Client, draft_id: UUID) -> IntakeState:
    """Reload a draft's current state (for resume)."""
    return _state_from_draft(_load_draft(db, draft_id))


def finalize(db: Client, user_id: UUID, draft_id: UUID, proposal: Proposal) -> UUID:
    """Promote the (user-edited) proposal into a real narrative + items + companies
    + notes, and mark the draft finalized. Idempotent on an already-finalized draft.

    Note: not atomic across statements (PostgREST has no multi-statement txn); a DB
    function would make it transactional later. Source rows / item citations land
    once the sources feature (C3/C4) exists — for now the kernel lives on the draft.
    """
    draft = _load_draft(db, draft_id)
    if draft["status"] == "finalized" and draft.get("narrative_id"):
        return UUID(draft["narrative_id"])  # already done

    # 1. the narrative
    narrative = narratives_service.create_for_user(
        db, user_id, NarrativeCreate(title=proposal.title, thesis=proposal.thesis)
    )
    nid = narrative.id

    # 2. items (bull/bear/catalyst/risk), batched with position per section
    position: dict[str, int] = defaultdict(int)
    item_rows = []
    for item in proposal.items:
        kind = item.kind.value
        item_rows.append({
            "narrative_id": str(nid),
            "kind": kind,
            "body": item.body,
            "event_date": item.event_date.isoformat() if item.event_date else None,
            "position": position[kind],
        })
        position[kind] += 1
    if item_rows:
        db.table("narrative_items").insert(item_rows).execute()

    # 3. companies (get-or-create + attach by exchange-qualified ticker)
    for company in proposal.companies:
        try:
            companies_service.attach(
                db, nid, CompanyAttach(ticker=company.ticker, exchange=company.exchange, name=company.name)
            )
        except Exception:
            continue  # skip a malformed company rather than fail the whole finalize

    # 4. open questions -> notes
    note_rows = [
        {"user_id": str(user_id), "narrative_id": str(nid), "body": q.strip()}
        for q in proposal.open_questions
        if q.strip()
    ]
    if note_rows:
        db.table("notes").insert(note_rows).execute()

    # 5. mark the draft finalized
    _update_draft(db, draft_id, {"status": "finalized", "narrative_id": str(nid)})
    return nid


# --- helpers ---------------------------------------------------------------

def _load_draft(db: Client, draft_id: UUID) -> dict:
    response = (
        db.table("narrative_drafts").select("*").eq("id", str(draft_id)).limit(1).execute()
    )
    if not response.data:
        raise DraftNotFound()
    return response.data[0]


def _update_draft(db: Client, draft_id: UUID, changes: dict) -> None:
    db.table("narrative_drafts").update(changes).eq("id", str(draft_id)).execute()


def _kernel_content(draft: dict) -> tuple[KernelKind, str]:
    kind = KernelKind(draft["kernel_kind"])
    if draft.get("kernel_raw"):
        return kind, draft["kernel_raw"]
    title, excerpt = draft.get("kernel_title"), draft.get("kernel_excerpt") or ""
    return kind, (f"{title}\n\n{excerpt}" if title else excerpt)


def _kernel_summary(draft: dict, kind: KernelKind) -> KernelSummary:
    excerpt = (draft.get("kernel_excerpt") or draft.get("kernel_raw") or "")[:300]
    return KernelSummary(kind=kind, title=draft.get("kernel_title"), excerpt=excerpt)


def _state_from_draft(draft: dict) -> IntakeState:
    kind = KernelKind(draft["kernel_kind"])
    proposal = Proposal.model_validate(draft["proposal"]) if draft.get("proposal") else None
    questions = None
    if draft["status"] == "collecting":
        for turn in reversed(draft["transcript"]):
            if "questions" in turn:
                questions = [Question.model_validate(q) for q in turn["questions"]]
                break
    return IntakeState(
        draft_id=draft["id"],
        status=draft["status"],
        kernel=_kernel_summary(draft, kind),
        round=draft["round"],
        questions=questions,
        proposal=proposal,
    )


def _format_qa(transcript: list[dict]) -> str:
    """Render the transcript's questions+answers into readable text for synthesis."""
    question_text: dict[str, str] = {}
    lines: list[str] = []
    for turn in transcript:
        for q in turn.get("questions", []):
            question_text[q["id"]] = q["question"]
        for a in turn.get("answers", []):
            label = question_text.get(a["question_id"], a["question_id"])
            selected = ", ".join(a.get("selected", []))
            free = a.get("free_text")
            if a.get("skipped"):
                given = "(skipped)"
            else:
                given = selected + (f" — {free}" if free else "") if (selected or free) else "(no answer)"
            lines.append(f"Q: {label}\nA: {given}")
    return "\n\n".join(lines) if lines else "(no answers provided)"
