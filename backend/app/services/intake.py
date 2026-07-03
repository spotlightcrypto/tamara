"""Guided narrative intake — the agentic flow.

Step 2 builds the front of the pipeline:
  create_draft(): classify + ingest the kernel (URL -> ingest_url; text -> as-is),
                  persist a narrative_drafts row, and generate the first round of
                  questions via the LLM.
  propose_questions(): the GLM structured call that turns a kernel (+ any prior
                  answers) into adaptive, POSITION-SEEKING questions.

Synthesis and the answer loop come in later steps.
"""

import hashlib
import re
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
from app.models.intake import MAX_COMPANIES
from app.providers import llm
from app.providers.ingest import ingest_url
from app.services import companies as companies_service
from app.services import narratives as narratives_service
from app.services import sources as sources_service

# Pull http(s) links out of free text so a text kernel that mentions a URL still
# records it as a source.
_URL_RE = re.compile(r"https?://[^\s<>\"')]+")

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
You are Tamara, an investment-research assistant. You turn a rough KERNEL (a link,
a tweet, or a note) into a SHORT, COMMITTED, PERSONAL investment take.

Decide whether you have enough to draft a useful, *positioned* take. If yes, set
ready=true and return no questions. Otherwise ask 4-6 sharp, NON-REDUNDANT
questions that pull out the user's OWN thinking and voice — not just facts.

Principles:
- Push toward a position. Infer the implied directional stance (long/short, the
  bet) from the kernel and aim questions at sharpening that bet — never produce a
  neutral, both-sides survey. If the kernel is directionless, ask what side the
  user wants to take.
- Cover the gaps among: the specific claim/direction, which companies or tickers,
  time horizon, the strongest point FOR it, what would break it, dated catalysts,
  and — importantly — the user's own edge/angle and why they care. Never ask what
  the kernel already answers.
- MIX the formats. Most questions offer 2-4 concrete options (label + short
  description) as quick taps. But ALWAYS include at least one OPEN question
  (open_ended=true, no options) that asks the user to answer in their OWN WORDS,
  e.g. "In a sentence or two, what's the real bet here?" or "What does the market
  get wrong?" These open answers capture their voice — favor them.

Output JSON matching the schema. Each question needs: id (stable lowercase slug),
header (<= 16 chars), question, options (label + optional description — EMPTY for
open questions), multi_select, allow_free_text, open_ended (true for the open,
answer-in-your-own-words questions)."""


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
You are Tamara. Turn the KERNEL and the user's answers into a SHORT, punchy,
PERSONAL investment take that commits to a position — the kind of thing someone
texts a smart friend, not a research report.

Voice & length:
- Write CASUALLY and plainly. Short sentences, contractions, everyday words. Skip
  finance jargon (no "re-rating", "multiple compression", "secular tailwind")
  UNLESS the user used it first. If a smart 12-year-old couldn't follow it, simplify.
- Keep it SHORT. The whole body is at most ~120 words. A few sharp points beat a
  complete survey — leave things out on purpose.
- Build it from the USER'S OWN WORDS. Echo their phrasing, their metaphors, their
  angle; lightly edit their strongest lines rather than paraphrasing them into
  generic prose. It should sound like THEM, not like a bank.

VARY your approach — do NOT use the same structure every time. Pick whatever
framing fits this take best (and lean toward the suggested lead angle if one is
given): the contrarian flip, the one number that matters, an analogy, a blunt
one-liner then reasons, the question the market is getting wrong, or a quick
story. Sometimes a short paragraph; sometimes two bullets; sometimes a line plus
a couple of reasons. Do NOT fall back on a rigid bull/bear/catalyst/risk template.

Produce, matching the schema:
- title: a short, casual title that names the bet.
- thesis: 1-2 casual sentences — the hook, the bet in plain words.
- positioning: ONE stance label capturing direction AND intensity, chosen from:
  megabull, permabull, normiebull, megabear, ultrabear.
- companies: the tickers the take is DIRECTLY about — ticker + exchange (e.g.
  CEG / NASDAQ), from the user's choices and the kernel (up to 8; don't pad).
  NEVER invent a ticker; if unsure, use the most likely.
- suggested_companies: up to 6 PROXIMATE peers to maybe add (competitors,
  suppliers, customers), each with a one-line `reason`. Never duplicate anything
  already in `companies`. Same ticker rules (never invent).
- body_md: the take itself as SHORT markdown (~120 words max), in the varied,
  casual style above. Use **bold** sparingly for the one or two lines that carry
  the bet. One "what would change my mind" beat is welcome but keep it tight. Do
  NOT fabricate facts, financials, or dates."""


# Distinct lead angles, rotated per-narrative so successive takes don't all open
# the same way. The model may override if another framing fits better.
_LEAD_ANGLES = [
    "the contrarian flip — name what the crowd believes, then why it's wrong",
    "the one number or fact that matters most",
    "an analogy that reframes the bet",
    "a blunt one-line call, then the reasons",
    "the question the market is getting wrong",
    "a quick concrete story or scenario",
]


def _pick_lead(seed: str) -> str:
    """Deterministically pick a lead angle from a seed, so different kernels lean
    different ways (variety) while a given kernel stays stable across retries."""
    digest = int(hashlib.md5(seed.encode("utf-8")).hexdigest(), 16)
    return _LEAD_ANGLES[digest % len(_LEAD_ANGLES)]


def _user_writing(kind: KernelKind, content: str, transcript: list[dict]) -> str:
    """Gather the user's OWN words to voice the take: their authored kernel (only
    if they wrote it — not a link/tweet we ingested) plus every free-text answer."""
    parts: list[str] = []
    if kind == KernelKind.text and content.strip():
        parts.append(content.strip())
    for turn in transcript:
        for a in turn.get("answers", []):
            free = (a.get("free_text") or "").strip()
            if free:
                parts.append(free)
    return "\n".join(f"- {p}" for p in parts) if parts else "(none provided)"


def synthesize_narrative(kind: KernelKind, content: str, transcript: list[dict]) -> Proposal:
    """Turn the kernel + answers into a short, casual, positioned take — voiced
    from the user's own words, with a rotated lead angle for variety."""
    writing = _user_writing(kind, content, transcript)
    lead = _pick_lead(content + writing)
    user_msg = (
        f'KERNEL (kind={kind.value}):\n"""\n{content[:6000]}\n"""\n\n'
        f"Q&A:\n{_format_qa(transcript)}\n\n"
        f"USER'S OWN WORDS (echo this voice; build the take from it):\n{writing}\n\n"
        f"Suggested lead angle (use if it fits, else pick a better one): {lead}"
    )
    messages = [
        {"role": "system", "content": _SYNTH_SYSTEM},
        {"role": "user", "content": user_msg},
    ]
    # Higher temperature for rhetorical variety across takes.
    return llm.structured(messages, Proposal, role="synthesis", temperature=0.9)


def regenerate(db: Client, draft_id: UUID, current: Proposal, instructions: str) -> IntakeState:
    """Re-synthesize the proposal, given the user's current edited version plus
    free-text instructions for what to change. Feeds the current proposal back in
    as context so the model revises rather than starting from scratch."""
    draft = _load_draft(db, draft_id)
    kind, content = _kernel_content(draft)
    transcript = list(draft["transcript"])
    writing = _user_writing(kind, content, transcript)
    messages = [
        {"role": "system", "content": _SYNTH_SYSTEM},
        {
            "role": "user",
            "content": (
                f'KERNEL (kind={kind.value}):\n"""\n{content[:6000]}\n"""\n\n'
                f"Q&A:\n{_format_qa(transcript)}\n\n"
                f"USER'S OWN WORDS (echo this voice):\n{writing}\n\n"
                f"CURRENT DRAFT (revise this, keep what still holds; stay short and casual):\n"
                f"{current.model_dump_json(indent=2)}\n\n"
                f"REVISION INSTRUCTIONS:\n{instructions.strip()}"
            ),
        },
    ]
    proposal = llm.structured(messages, Proposal, role="synthesis", temperature=0.9)
    _update_draft(db, draft_id, {"proposal": proposal.model_dump(mode="json"), "status": "proposed"})
    summary = _kernel_summary(draft, kind)
    return IntakeState(
        draft_id=draft["id"], status="proposed", kernel=summary, round=draft["round"], proposal=proposal
    )


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
    """Promote the (user-edited) proposal into a real narrative + items + companies,
    and mark the draft finalized. Idempotent on an already-finalized draft.

    Note: not atomic across statements (PostgREST has no multi-statement txn); a DB
    function would make it transactional later. Source rows / item citations land
    once the sources feature (C3/C4) exists — for now the kernel lives on the draft.
    """
    draft = _load_draft(db, draft_id)
    if draft["status"] == "finalized" and draft.get("narrative_id"):
        return UUID(draft["narrative_id"])  # already done

    # 1. the narrative — content lives in the markdown body, with a stance label
    narrative = narratives_service.create_for_user(
        db,
        user_id,
        NarrativeCreate(
            title=proposal.title,
            thesis=proposal.thesis,
            body_md=proposal.body_md,
            positioning=proposal.positioning,
        ),
    )
    nid = narrative.id

    # 2. companies (get-or-create + attach by exchange-qualified ticker), capped
    #    at MAX_COMPANIES — a narrative is about at most 8 companies.
    for company in proposal.companies[:MAX_COMPANIES]:
        try:
            companies_service.attach(
                db, nid, CompanyAttach(ticker=company.ticker, exchange=company.exchange, name=company.name)
            )
        except Exception:
            continue  # skip a malformed company rather than fail the whole finalize

    # 3. sources — record the kernel's link(s) so the narrative shows its origin.
    for url, title in _kernel_sources(draft):
        try:
            sources_service.add(db, nid, url, title)
        except Exception:
            continue

    # NOTE: we deliberately do NOT create notes here. Notes are post-publication
    # commentary the user adds *after* a narrative exists — not intake output.
    # Open questions live inside the markdown body, so nothing is lost.

    # 4. mark the draft finalized
    _update_draft(db, draft_id, {"status": "finalized", "narrative_id": str(nid)})
    return nid


# --- helpers ---------------------------------------------------------------

def _kernel_sources(draft: dict) -> list[tuple[str, str | None]]:
    """The link(s) to record as sources for this draft's kernel.

    A URL kernel yields one source with the title we ingested (a "few words"
    name). A text kernel yields any http(s) links found in the pasted text
    (titled by hostname downstream). Returns (url, title) pairs, de-duplicated.
    """
    out: list[tuple[str, str | None]] = []
    seen: set[str] = set()
    if draft.get("kernel_url"):
        out.append((draft["kernel_url"], draft.get("kernel_title")))
        seen.add(draft["kernel_url"])
    for match in _URL_RE.findall(draft.get("kernel_raw") or ""):
        if match not in seen:
            out.append((match, None))
            seen.add(match)
    return out


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
