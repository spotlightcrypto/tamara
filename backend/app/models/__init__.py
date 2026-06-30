"""API models, organized by domain.

Models live in submodules (narratives, items, users), but are re-exported here
so the rest of the app can keep importing `from app.models import X` regardless
of which file a model actually lives in. Add new models to a submodule and list
them here.
"""

from app.models.companies import Company, CompanyAttach
from app.models.intake import (
    Answer,
    Confidence,
    IngestReason,
    IngestResult,
    IntakeAnswerRequest,
    IntakeStart,
    IntakeState,
    Kernel,
    KernelKind,
    KernelSummary,
    Proposal,
    ProposalCompany,
    ProposalItem,
    Question,
    QuestionOption,
)
from app.models.items import (
    Item,
    ItemCreate,
    ItemKind,
    ItemMove,
    ItemUpdate,
)
from app.models.narratives import (
    Narrative,
    NarrativeCreate,
    NarrativeUpdate,
)
from app.models.notes import Note, NoteCreate, NoteUpdate
from app.models.users import CurrentUser

__all__ = [
    "Answer",
    "Company",
    "CompanyAttach",
    "Confidence",
    "CurrentUser",
    "IngestReason",
    "IngestResult",
    "IntakeAnswerRequest",
    "IntakeStart",
    "IntakeState",
    "Item",
    "ItemCreate",
    "ItemKind",
    "ItemMove",
    "ItemUpdate",
    "Kernel",
    "KernelKind",
    "KernelSummary",
    "Proposal",
    "ProposalCompany",
    "ProposalItem",
    "Question",
    "QuestionOption",
    "Narrative",
    "NarrativeCreate",
    "NarrativeUpdate",
    "Note",
    "NoteCreate",
    "NoteUpdate",
]
