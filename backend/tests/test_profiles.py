"""Tests for profiles / usernames and the create-content gate."""


def _clear_profile(db, user_id):
    db.table("profiles").delete().eq("id", user_id).execute()


def test_check_claim_and_rename(client, db, user_id):
    _clear_profile(db, user_id)

    # available before claiming
    assert client.get("/usernames/check?u=tamara_tester").json()["available"] is True

    # claim it
    r = client.post("/me/username", json={"username": "Tamara_Tester"})  # mixed case
    assert r.status_code == 200
    assert r.json()["username"] == "tamara_tester"  # normalized lowercase

    # /me/profile reflects it (and returns the caller's own email)
    me = client.get("/me/profile").json()
    assert me["username"] == "tamara_tester"
    assert me["email"]  # the only place an email is returned — to its owner

    # now it's taken (even for a re-check)
    assert client.get("/usernames/check?u=tamara_tester").json()["available"] is False

    # rename works (same row, immutable id) — nothing else references the string
    r2 = client.post("/me/username", json={"username": "tamara_v2"})
    assert r2.status_code == 200 and r2.json()["username"] == "tamara_v2"
    assert client.get("/me/profile").json()["username"] == "tamara_v2"

    _clear_profile(db, user_id)


def test_username_validation(client, db, user_id):
    _clear_profile(db, user_id)
    # too short / reserved / bad chars are not available
    assert client.get("/usernames/check?u=ab").json()["available"] is False
    assert client.get("/usernames/check?u=admin").json()["available"] is False
    assert client.get("/usernames/check?u=1abc").json()["available"] is False  # must start with letter
    # claiming an invalid one is a 422
    assert client.post("/me/username", json={"username": "admin"}).status_code == 422
    _clear_profile(db, user_id)


def test_me_profile_null_until_claimed(client, db, user_id):
    _clear_profile(db, user_id)
    me = client.get("/me/profile").json()
    assert me["username"] is None


def test_create_requires_username(gated_client, db, user_id):
    """With the real gate, a user without a username can't create content."""
    _clear_profile(db, user_id)
    assert gated_client.post("/narratives", json={"title": "no username"}).status_code == 403
    assert gated_client.post(
        "/narratives/intake", json={"kernel": {"kind": "text", "raw_text": "x"}}
    ).status_code == 403
