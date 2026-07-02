"""Models for the guided narrative intake (kernel -> questionnaire -> proposal).

Two layers:
- The KERNEL the user submits, and the QUESTIONS/ANSWERS exchanged.
- The synthesized PROPOSAL (an editable draft narrative) the user accepts.

The proposal is what the LLM returns via structured output; on finalize it's
promoted to real narratives + items + companies + a source.
"""

from datetime import date
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.items import ItemKind


class KernelKind(str, Enum):
    text = "text"
    url = "url"
    tweet = "tweet"
    document = "document"


class Kernel(BaseModel):
    """What the user submits to start an intake."""

    kind: KernelKind
    raw_text: str | None = None
    url: str | None = None


class IngestReason(str, Enum):
    """Why a URL couldn't be turned into usable content (for the error state)."""

    invalid_url = "invalid_url"
    unreachable = "unreachable"
    blocked = "blocked"        # anti-bot / 403
    paywalled = "paywalled"
    empty = "empty"            # loaded but no substantive content ("useless")
    unsupported = "unsupported"


class IngestResult(BaseModel):
    """Outcome of ingesting a URL. Never raised — always returned, so intake can
    degrade to a paste-fallback rather than crash."""

    ok: bool
    source_kind: KernelKind  # url | tweet
    url: str
    title: str | None = None
    excerpt: str = ""
    reason: IngestReason | None = None


# --- Questionnaire ---------------------------------------------------------

class QuestionOption(BaseModel):
    label: str
    description: str | None = None


class Question(BaseModel):
    id: str
    header: str  # short chip label
    question: str
    options: list[QuestionOption] = []
    multi_select: bool = False
    allow_free_text: bool = True


class Answer(BaseModel):
    question_id: str
    selected: list[str] = []      # chosen option labels
    free_text: str | None = None
    skipped: bool = False


# --- Synthesized proposal --------------------------------------------------

# The auto-generated stance labels the agent picks from. Stored on the narrative
# and freely editable by the user, so this is guidance, not a hard enum.
POSITIONING_LABELS = ["megabull", "permabull", "normiebull", "megabear", "ultrabear"]


class ProposalCompany(BaseModel):
    ticker: str
    exchange: str
    name: str | None = None
    reason: str | None = None  # why it's in the narrative


class ProposalItem(BaseModel):
    kind: ItemKind  # bull | bear | catalyst | risk
    body: str
    event_date: date | None = None
    cite: str | None = None  # "kernel" if supported by the kernel text, else null


MAX_COMPANIES = 8  # a narrative is about at most this many companies


class Proposal(BaseModel):
    """The committed, directional draft narrative. The thesis takes a position;
    the body is one markdown doc grouping the bull case (THE case), the bear/risk
    counter, catalysts, and open questions."""

    title: str
    thesis: str
    # An auto-generated stance label from POSITIONING_LABELS, editable to anything.
    positioning: str = "normiebull"
    # The companies the thesis is directly about (1..MAX_COMPANIES).
    companies: list[ProposalCompany] = []
    # Proximate / possibly-relevant peers the agent offers for the user to ADD —
    # not committed to the thesis, just candidates surfaced in the review step.
    suggested_companies: list[ProposalCompany] = []
    # The full narrative body as an editable markdown document.
    body_md: str = ""


# --- API request / response shapes ----------------------------------------

class IntakeStart(BaseModel):
    kernel: Kernel


class IntakeAnswerRequest(BaseModel):
    answers: list[Answer] = []
    finish_now: bool = False  # skip remaining questions, synthesize now


class IntakeFinalize(BaseModel):
    """The user-edited proposal, accepted -> promote to a real narrative."""

    proposal: Proposal


class IntakeRegenerate(BaseModel):
    """Re-run synthesis using the current edited proposal + free-text instructions."""

    proposal: Proposal
    instructions: str = Field(min_length=1, max_length=2000)


class KernelSummary(BaseModel):
    kind: KernelKind
    title: str | None = None
    excerpt: str | None = None


class IntakeState(BaseModel):
    """Returned after each intake step: either more questions, or a proposal."""

    draft_id: UUID
    status: str
    kernel: KernelSummary
    round: int
    questions: list[Question] | None = None
    proposal: Proposal | None = None
