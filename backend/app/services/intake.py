"""Guided narrative intake — the agentic flow.

Step 2 builds the front of the pipeline:
  create_draft(): classify + ingest the kernel (URL -> ingest_url; text -> as-is),
                  persist a narrative_drafts row, and generate the first round of
                  questions via the LLM.
  propose_questions(): the GLM structured call that turns a kernel (+ any prior
                  answers) into adaptive, POSITION-SEEKING questions.

Synthesis and the answer loop come in later steps.
"""

from uuid import UUID

from pydantic import BaseModel
from supabase import Client

from app.models import (
    IngestResult,
    IntakeState,
    Kernel,
    KernelKind,
    KernelSummary,
    Question,
)
from app.providers import llm
from app.providers.ingest import ingest_url


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
