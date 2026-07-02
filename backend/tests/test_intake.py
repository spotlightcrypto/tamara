"""Tests for the intake state machine.

The LLM boundary is mocked (propose_questions / synthesize_narrative return
canned outputs) so these are deterministic and cost nothing; the DB side runs
against real Supabase (like the rest of our suite).
"""

from app.models import (
    IngestReason,
    IngestResult,
    KernelKind,
    Proposal,
    ProposalCompany,
    Question,
    QuestionOption,
)
from app.services.intake import QuestionSet

MISSING = "00000000-0000-0000-0000-000000000000"

CANNED_QUESTIONS = QuestionSet(
    ready=False,
    questions=[
        Question(
            id="q_dir",
            header="Direction",
            question="Long or short?",
            options=[QuestionOption(label="Long"), QuestionOption(label="Short")],
        )
    ],
)

CANNED_PROPOSAL = Proposal(
    title="Test Thesis",
    thesis="Long the thing.",
    positioning="megabull",
    companies=[ProposalCompany(ticker="NVDA", exchange="NASDAQ", name="NVIDIA")],
    body_md="## Bull\n- up point\n\n## Bear\n- down point",
)


def _mock_llm(monkeypatch):
    monkeypatch.setattr("app.services.intake.propose_questions", lambda *a, **k: CANNED_QUESTIONS)
    monkeypatch.setattr("app.services.intake.synthesize_narrative", lambda *a, **k: CANNED_PROPOSAL)


def _start(client, monkeypatch, text="AI power crunch, long nuclear"):
    _mock_llm(monkeypatch)
    r = client.post("/narratives/intake", json={"kernel": {"kind": "text", "raw_text": text}})
    assert r.status_code == 201
    return r.json()


def _delete_draft(db, draft_id):
    db.table("narrative_drafts").delete().eq("id", draft_id).execute()


def test_start_creates_draft_and_logs_questions(client, db, monkeypatch):
    state = _start(client, monkeypatch)
    assert state["status"] == "collecting" and state["round"] == 1
    assert len(state["questions"]) == 1 and state["questions"][0]["header"] == "Direction"

    row = db.table("narrative_drafts").select("transcript").eq("id", state["draft_id"]).execute().data[0]
    assert row["transcript"][0]["round"] == 1 and "questions" in row["transcript"][0]
    _delete_draft(db, state["draft_id"])


def test_answer_finish_now_synthesizes(client, db, monkeypatch):
    state = _start(client, monkeypatch)
    did = state["draft_id"]
    r = client.post(
        f"/narratives/intake/{did}/answer",
        json={"answers": [{"question_id": "q_dir", "selected": ["Long"]}], "finish_now": True},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "proposed" and body["proposal"]["title"] == "Test Thesis"

    row = db.table("narrative_drafts").select("transcript,status").eq("id", did).execute().data[0]
    assert any("answers" in turn for turn in row["transcript"])  # answers logged
    assert row["status"] == "proposed"
    _delete_draft(db, did)


def test_answer_advances_rounds_then_synthesizes_at_max(client, db, monkeypatch):
    state = _start(client, monkeypatch)
    did = state["draft_id"]
    ans = {"answers": [{"question_id": "q_dir", "selected": ["Long"]}]}
    r1 = client.post(f"/narratives/intake/{did}/answer", json=ans).json()
    assert r1["status"] == "collecting" and r1["round"] == 2
    r2 = client.post(f"/narratives/intake/{did}/answer", json=ans).json()
    assert r2["status"] == "collecting" and r2["round"] == 3
    r3 = client.post(f"/narratives/intake/{did}/answer", json=ans).json()
    assert r3["status"] == "proposed"  # MAX_ROUNDS reached -> synthesize
    _delete_draft(db, did)


def test_finalize_creates_narrative_and_children_idempotent(client, db, monkeypatch):
    state = _start(client, monkeypatch)
    did = state["draft_id"]
    answered = client.post(
        f"/narratives/intake/{did}/answer",
        json={"answers": [{"question_id": "q_dir", "selected": ["Long"]}], "finish_now": True},
    ).json()
    proposal = answered["proposal"]

    r = client.post(f"/narratives/intake/{did}/finalize", json={"proposal": proposal})
    assert r.status_code == 201
    nid = r.json()["narrative_id"]

    narr = db.table("narratives").select("title,body_md,positioning").eq("id", nid).execute().data[0]
    companies = client.get(f"/narratives/{nid}/companies").json()
    notes = db.table("notes").select("body").eq("narrative_id", nid).execute().data
    draft = db.table("narrative_drafts").select("status,narrative_id").eq("id", did).execute().data[0]

    assert narr["title"] == "Test Thesis"
    assert narr["positioning"] == "megabull"
    assert "## Bull" in narr["body_md"] and "up point" in narr["body_md"]
    assert [c["symbol"] for c in companies] == ["NVDA:NASDAQ"]
    # Notes are post-publication only — finalize must NOT seed any.
    assert len(notes) == 0
    assert draft["status"] == "finalized" and draft["narrative_id"] == nid

    # plain text kernel (no link) -> no sources recorded
    assert client.get(f"/narratives/{nid}/sources").json() == []

    # idempotent — re-finalize returns the same narrative, no duplicate
    nid2 = client.post(f"/narratives/intake/{did}/finalize", json={"proposal": proposal}).json()["narrative_id"]
    assert nid2 == nid

    db.table("narratives").delete().eq("id", nid).execute()  # cascades items/notes/links
    _delete_draft(db, did)


def test_finalize_records_kernel_link_as_source(client, db, monkeypatch):
    """A link in the kernel is captured as a source on the finished narrative,
    idempotently (re-finalize doesn't duplicate it)."""
    url = "https://example.com/nvda-thesis"
    state = _start(client, monkeypatch, text=f"long NVDA, see {url}")
    did = state["draft_id"]
    proposal = client.post(
        f"/narratives/intake/{did}/answer",
        json={"answers": [{"question_id": "q_dir", "selected": ["Long"]}], "finish_now": True},
    ).json()["proposal"]

    nid = client.post(f"/narratives/intake/{did}/finalize", json={"proposal": proposal}).json()["narrative_id"]

    sources = client.get(f"/narratives/{nid}/sources").json()
    assert [s["url"] for s in sources] == [url]
    assert sources[0]["title"] == "example.com"  # hostname fallback name

    # re-finalize is idempotent — still exactly one source
    client.post(f"/narratives/intake/{did}/finalize", json={"proposal": proposal})
    assert len(client.get(f"/narratives/{nid}/sources").json()) == 1

    db.table("narratives").delete().eq("id", nid).execute()
    _delete_draft(db, did)


def test_start_bad_url_returns_structured_422(client, monkeypatch):
    monkeypatch.setattr(
        "app.services.intake.ingest_url",
        lambda url: IngestResult(ok=False, source_kind=KernelKind.url, url=url, reason=IngestReason.blocked),
    )
    r = client.post("/narratives/intake", json={"kernel": {"kind": "url", "url": "https://paywalled.example/x"}})
    assert r.status_code == 422
    assert r.json()["detail"]["reason"] == "blocked"


def test_resume_get_draft(client, db, monkeypatch):
    state = _start(client, monkeypatch)
    did = state["draft_id"]
    body = client.get(f"/narratives/intake/{did}").json()
    assert body["status"] == "collecting" and body["draft_id"] == did
    assert body["questions"][0]["header"] == "Direction"
    _delete_draft(db, did)


def test_regenerate_revises_proposal(client, db, monkeypatch):
    """Regenerate feeds the current proposal + instructions back to synthesis and
    returns the revised proposal (persisted on the draft)."""
    state = _start(client, monkeypatch)
    did = state["draft_id"]
    proposal = client.post(
        f"/narratives/intake/{did}/answer",
        json={"answers": [{"question_id": "q_dir", "selected": ["Long"]}], "finish_now": True},
    ).json()["proposal"]

    revised = CANNED_PROPOSAL.model_copy(update={"title": "Revised Thesis"})
    monkeypatch.setattr("app.services.intake.llm.structured", lambda *a, **k: revised)

    r = client.post(
        f"/narratives/intake/{did}/regenerate",
        json={"proposal": proposal, "instructions": "make the title sharper"},
    )
    assert r.status_code == 200
    assert r.json()["proposal"]["title"] == "Revised Thesis"

    saved = db.table("narrative_drafts").select("proposal").eq("id", did).execute().data[0]
    assert saved["proposal"]["title"] == "Revised Thesis"
    _delete_draft(db, did)


def test_answer_missing_draft_returns_404(client):
    r = client.post(f"/narratives/intake/{MISSING}/answer", json={"answers": []})
    assert r.status_code == 404


def test_intake_requires_auth(unauth_client):
    r = unauth_client.post("/narratives/intake", json={"kernel": {"kind": "text", "raw_text": "x"}})
    assert r.status_code == 401
