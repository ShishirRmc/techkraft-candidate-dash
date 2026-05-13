"""Core API tests for the TechKraft Candidate Dashboard."""

import time
from datetime import datetime, timezone

from app.models import Candidate, Score, User
from app.auth import hash_password


def test_register_always_assigns_reviewer_role(client):
    """Registration NEVER accepts role from client — always assigns reviewer."""
    res = client.post("/auth/register", json={
        "email": "hacker@example.com",
        "password": "password123",
    })
    assert res.status_code == 201
    data = res.json()
    assert data["role"] == "reviewer"
    assert data["email"] == "hacker@example.com"


def test_register_rejects_short_password(client):
    """Registration returns 422 when password is less than 6 characters."""
    res = client.post("/auth/register", json={
        "email": "short@example.com",
        "password": "abc",
    })
    assert res.status_code == 422
    data = res.json()
    assert "detail" in data


def test_create_candidate_and_verify_response(client, auth_headers, setup_db):
    """Create a candidate via seeding, then verify we can retrieve it."""
    from tests.conftest import TestingSessionLocal

    db = TestingSessionLocal()
    candidate = Candidate(
        name="Test Candidate",
        email="candidate@test.com",
        role_applied="Backend Engineer",
        status="new",
        skills="Python,FastAPI",
    )
    db.add(candidate)
    db.commit()
    db.refresh(candidate)
    candidate_id = candidate.id
    db.close()

    res = client.get(f"/candidates/{candidate_id}", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["name"] == "Test Candidate"
    assert data["email"] == "candidate@test.com"
    assert data["role_applied"] == "Backend Engineer"
    assert data["status"] == "new"
    assert data["skills"] == "Python,FastAPI"


def test_reviewer_cannot_see_other_reviewers_scores(client, setup_db):
    """A reviewer should only see their own scores, not another reviewer's."""
    from tests.conftest import TestingSessionLocal

    client.post("/auth/register", json={"email": "rev1@test.com", "password": "pass123"})
    client.post("/auth/register", json={"email": "rev2@test.com", "password": "pass123"})

    res1 = client.post("/auth/login", json={"email": "rev1@test.com", "password": "pass123"})
    token1 = res1.json()["access_token"]

    res2 = client.post("/auth/login", json={"email": "rev2@test.com", "password": "pass123"})
    token2 = res2.json()["access_token"]

    db = TestingSessionLocal()
    candidate = Candidate(
        name="Shared Candidate",
        email="shared@test.com",
        role_applied="Frontend Engineer",
        status="reviewing",
        skills="React",
    )
    db.add(candidate)
    db.commit()
    db.refresh(candidate)
    candidate_id = candidate.id
    db.close()

    client.post(
        f"/candidates/{candidate_id}/scores",
        json={"category": "technical", "score": 5, "note": "Rev1 note"},
        headers={"Authorization": f"Bearer {token1}"},
    )

    client.post(
        f"/candidates/{candidate_id}/scores",
        json={"category": "communication", "score": 3, "note": "Rev2 note"},
        headers={"Authorization": f"Bearer {token2}"},
    )

    res = client.get(
        f"/candidates/{candidate_id}",
        headers={"Authorization": f"Bearer {token1}"},
    )
    data = res.json()
    assert len(data["scores"]) == 1
    assert data["scores"][0]["category"] == "technical"

    res = client.get(
        f"/candidates/{candidate_id}",
        headers={"Authorization": f"Bearer {token2}"},
    )
    data = res.json()
    assert len(data["scores"]) == 1
    assert data["scores"][0]["category"] == "communication"


def test_summary_endpoint_returns_valid_response_with_delay(client, auth_headers, setup_db):
    """Summary endpoint should return a valid response after a 2+ second simulated delay."""
    from tests.conftest import TestingSessionLocal

    db = TestingSessionLocal()
    candidate = Candidate(
        name="Summary Test",
        email="summary@test.com",
        role_applied="Backend Engineer",
        status="new",
        skills="Python",
    )
    db.add(candidate)
    db.commit()
    db.refresh(candidate)
    candidate_id = candidate.id
    db.close()

    start = time.time()
    res = client.post(f"/candidates/{candidate_id}/summary", headers=auth_headers)
    elapsed = time.time() - start

    assert res.status_code == 200
    data = res.json()
    assert "summary" in data
    assert len(data["summary"]) > 20
    assert "Summary Test" in data["summary"]
    assert elapsed >= 2.0


def test_pagination_works(client, auth_headers, setup_db):
    """Seed 15 candidates, verify pagination with explicit page_size=10."""
    from tests.conftest import TestingSessionLocal

    db = TestingSessionLocal()
    for i in range(15):
        db.add(Candidate(
            name=f"Candidate {i}",
            email=f"c{i}@test.com",
            role_applied="Engineer",
            status="new",
        ))
    db.commit()
    db.close()

    # Explicitly pass page_size=10 to test pagination behavior
    res = client.get("/candidates?page=1&page_size=10", headers=auth_headers)
    data = res.json()
    assert data["total"] == 15
    assert len(data["items"]) == 10
    assert data["page"] == 1
    assert data["page_size"] == 10

    res = client.get("/candidates?page=2&page_size=10", headers=auth_headers)
    data = res.json()
    assert len(data["items"]) == 5
    assert data["page"] == 2

    # Verify default page_size is 20 (all 15 fit on one page)
    res = client.get("/candidates", headers=auth_headers)
    data = res.json()
    assert data["page_size"] == 20
    assert len(data["items"]) == 15


def test_filter_by_status(client, auth_headers, setup_db):
    """Seed candidates with different statuses, filter by one, verify only matching return."""
    from tests.conftest import TestingSessionLocal

    db = TestingSessionLocal()
    db.add(Candidate(name="New One", email="n@t.com", role_applied="Eng", status="new"))
    db.add(Candidate(name="New Two", email="n2@t.com", role_applied="Eng", status="new"))
    db.add(Candidate(name="Reviewing", email="r@t.com", role_applied="Eng", status="reviewing"))
    db.add(Candidate(name="Offered", email="o@t.com", role_applied="Eng", status="offered"))
    db.commit()
    db.close()

    res = client.get("/candidates?status=new", headers=auth_headers)
    data = res.json()
    assert data["total"] == 2
    assert all(item["status"] == "new" for item in data["items"])

    res = client.get("/candidates?status=offered", headers=auth_headers)
    data = res.json()
    assert data["total"] == 1
    assert data["items"][0]["name"] == "Offered"


def test_soft_deleted_candidate_not_in_list(client, auth_headers, setup_db):
    """A candidate with deleted_at set should not appear in the list endpoint."""
    from tests.conftest import TestingSessionLocal

    db = TestingSessionLocal()
    db.add(Candidate(
        name="Visible",
        email="v@t.com",
        role_applied="Eng",
        status="new",
    ))
    db.add(Candidate(
        name="Deleted",
        email="d@t.com",
        role_applied="Eng",
        status="new",
        deleted_at=datetime.now(timezone.utc),
    ))
    db.commit()
    db.close()

    res = client.get("/candidates", headers=auth_headers)
    data = res.json()
    assert data["total"] == 1
    assert data["items"][0]["name"] == "Visible"


def test_admin_sees_all_reviewers_scores(client, setup_db):
    """Admin should see scores from all reviewers for a candidate."""
    from tests.conftest import TestingSessionLocal

    # Create admin directly in DB
    from app.auth import hash_password
    db = TestingSessionLocal()
    admin = User(email="admin@test.com", hashed_password=hash_password("admin123"), role="admin")
    db.add(admin)
    db.commit()
    db.close()

    # Create two reviewers
    client.post("/auth/register", json={"email": "r1@test.com", "password": "pass123"})
    client.post("/auth/register", json={"email": "r2@test.com", "password": "pass123"})

    res1 = client.post("/auth/login", json={"email": "r1@test.com", "password": "pass123"})
    token1 = res1.json()["access_token"]

    res2 = client.post("/auth/login", json={"email": "r2@test.com", "password": "pass123"})
    token2 = res2.json()["access_token"]

    admin_res = client.post("/auth/login", json={"email": "admin@test.com", "password": "admin123"})
    admin_token = admin_res.json()["access_token"]

    # Seed a candidate
    db = TestingSessionLocal()
    candidate = Candidate(
        name="Admin View Test",
        email="avt@test.com",
        role_applied="Engineer",
        status="reviewing",
    )
    db.add(candidate)
    db.commit()
    db.refresh(candidate)
    candidate_id = candidate.id
    db.close()

    # Both reviewers score
    client.post(
        f"/candidates/{candidate_id}/scores",
        json={"category": "technical", "score": 5},
        headers={"Authorization": f"Bearer {token1}"},
    )
    client.post(
        f"/candidates/{candidate_id}/scores",
        json={"category": "communication", "score": 4},
        headers={"Authorization": f"Bearer {token2}"},
    )

    # Admin sees both scores
    res = client.get(
        f"/candidates/{candidate_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    data = res.json()
    assert len(data["scores"]) == 2
    categories = {s["category"] for s in data["scores"]}
    assert categories == {"technical", "communication"}


def test_duplicate_score_returns_409(client, auth_headers, setup_db):
    """Submitting the same category score twice should return 409 Conflict."""
    from tests.conftest import TestingSessionLocal

    db = TestingSessionLocal()
    candidate = Candidate(
        name="Dup Test",
        email="dup@test.com",
        role_applied="Engineer",
        status="new",
    )
    db.add(candidate)
    db.commit()
    db.refresh(candidate)
    candidate_id = candidate.id
    db.close()

    # First score succeeds
    res = client.post(
        f"/candidates/{candidate_id}/scores",
        json={"category": "technical", "score": 4},
        headers=auth_headers,
    )
    assert res.status_code == 201

    # Duplicate score returns 409
    res = client.post(
        f"/candidates/{candidate_id}/scores",
        json={"category": "technical", "score": 5},
        headers=auth_headers,
    )
    assert res.status_code == 409
    assert "already scored" in res.json()["detail"]


def test_admin_can_edit_internal_notes(client, setup_db):
    """Admin can PATCH internal_notes and the change persists."""
    from tests.conftest import TestingSessionLocal
    from app.auth import hash_password

    db = TestingSessionLocal()
    admin = User(email="admin@notes.com", hashed_password=hash_password("admin123"), role="admin")
    db.add(admin)
    candidate = Candidate(
        name="Notes Target",
        email="notes@test.com",
        role_applied="Engineer",
        status="new",
        internal_notes="Original notes",
    )
    db.add(candidate)
    db.commit()
    db.refresh(candidate)
    candidate_id = candidate.id
    db.close()

    admin_res = client.post("/auth/login", json={"email": "admin@notes.com", "password": "admin123"})
    admin_token = admin_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {admin_token}"}

    # Update notes
    res = client.patch(
        f"/candidates/{candidate_id}/notes",
        json={"internal_notes": "Updated by admin"},
        headers=headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["internal_notes"] == "Updated by admin"

    # Verify persistence via GET
    res = client.get(f"/candidates/{candidate_id}", headers=headers)
    assert res.json()["internal_notes"] == "Updated by admin"


def test_reviewer_cannot_edit_internal_notes(client, auth_headers, setup_db):
    """Reviewer gets 403 when trying to PATCH internal_notes."""
    from tests.conftest import TestingSessionLocal

    db = TestingSessionLocal()
    candidate = Candidate(
        name="Forbidden Target",
        email="forbidden@test.com",
        role_applied="Engineer",
        status="new",
    )
    db.add(candidate)
    db.commit()
    db.refresh(candidate)
    candidate_id = candidate.id
    db.close()

    res = client.patch(
        f"/candidates/{candidate_id}/notes",
        json={"internal_notes": "Hacker notes"},
        headers=auth_headers,
    )
    assert res.status_code == 403
    assert "Admin access required" in res.json()["detail"]


def test_admin_can_delete_score(client, setup_db):
    """Admin can delete a score via DELETE endpoint."""
    from tests.conftest import TestingSessionLocal
    from app.auth import hash_password

    # Create admin
    db = TestingSessionLocal()
    admin = User(email="admin@del.com", hashed_password=hash_password("admin123"), role="admin")
    db.add(admin)
    db.commit()
    db.close()

    # Create reviewer
    client.post("/auth/register", json={"email": "rev@del.com", "password": "pass123"})
    rev_res = client.post("/auth/login", json={"email": "rev@del.com", "password": "pass123"})
    rev_token = rev_res.json()["access_token"]

    # Login admin
    admin_res = client.post("/auth/login", json={"email": "admin@del.com", "password": "admin123"})
    admin_token = admin_res.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # Create candidate
    db = TestingSessionLocal()
    candidate = Candidate(
        name="Delete Score Target",
        email="dst@test.com",
        role_applied="Engineer",
        status="new",
    )
    db.add(candidate)
    db.commit()
    db.refresh(candidate)
    candidate_id = candidate.id
    db.close()

    # Reviewer submits a score
    score_res = client.post(
        f"/candidates/{candidate_id}/scores",
        json={"category": "technical", "score": 4, "note": "Good"},
        headers={"Authorization": f"Bearer {rev_token}"},
    )
    assert score_res.status_code == 201
    score_id = score_res.json()["id"]

    # Admin deletes the score
    del_res = client.delete(
        f"/candidates/{candidate_id}/scores/{score_id}",
        headers=admin_headers,
    )
    assert del_res.status_code == 204

    # Verify scores list is empty
    get_res = client.get(f"/candidates/{candidate_id}", headers=admin_headers)
    assert get_res.status_code == 200
    assert get_res.json()["scores"] == []


def test_reviewer_cannot_delete_score(client, setup_db):
    """Reviewer gets 403 when trying to DELETE a score."""
    from tests.conftest import TestingSessionLocal

    # Create reviewer
    client.post("/auth/register", json={"email": "rev@forbid.com", "password": "pass123"})
    rev_res = client.post("/auth/login", json={"email": "rev@forbid.com", "password": "pass123"})
    rev_token = rev_res.json()["access_token"]
    rev_headers = {"Authorization": f"Bearer {rev_token}"}

    # Create candidate
    db = TestingSessionLocal()
    candidate = Candidate(
        name="Forbid Target",
        email="ft@test.com",
        role_applied="Engineer",
        status="new",
    )
    db.add(candidate)
    db.commit()
    db.refresh(candidate)
    candidate_id = candidate.id
    db.close()

    # Reviewer submits a score
    score_res = client.post(
        f"/candidates/{candidate_id}/scores",
        json={"category": "technical", "score": 3},
        headers=rev_headers,
    )
    assert score_res.status_code == 201
    score_id = score_res.json()["id"]

    # Reviewer tries to delete — should get 403
    del_res = client.delete(
        f"/candidates/{candidate_id}/scores/{score_id}",
        headers=rev_headers,
    )
    assert del_res.status_code == 403
    assert "Admin access required" in del_res.json()["detail"]
