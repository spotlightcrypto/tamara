"""API models, organized by domain.

Models live in submodules (narratives, items, users), but are re-exported here
so the rest of the app can keep importing `from app.models import X` regardless
of which file a model actually lives in. Add new models to a submodule and list
them here.
"""

from app.models.companies import Company, CompanyAttach
from app.models.intake import (
    Answer,
    IngestReason,
    IngestResult,
    IntakeAnswerRequest,
    IntakeFinalize,
    IntakeRegenerate,
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
    NarrativeSummary,
    NarrativeUpdate,
)
from app.models.notes import Note, NoteCreate, NoteUpdate
from app.models.prices import PricePerformance
from app.models.profiles import Me, Profile, UsernameCheck, UsernameClaim
from app.models.sources import Source
from app.models.users import CurrentUser

__all__ = [
    "Answer",
    "Company",
    "CompanyAttach",
    "CurrentUser",
    "IngestReason",
    "IngestResult",
    "IntakeAnswerRequest",
    "IntakeFinalize",
    "IntakeRegenerate",
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
    "NarrativeSummary",
    "NarrativeUpdate",
    "Me",
    "Note",
    "NoteCreate",
    "NoteUpdate",
    "PricePerformance",
    "Profile",
    "Source",
    "UsernameCheck",
    "UsernameClaim",
]
