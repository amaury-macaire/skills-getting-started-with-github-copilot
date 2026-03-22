import copy
import pytest
from starlette.testclient import TestClient
import src.app as app_module
from src.app import app

client = TestClient(app, follow_redirects=False)

# Snapshot of the original activities state captured at import time
_original_activities = copy.deepcopy(app_module.activities)


@pytest.fixture(autouse=True)
def reset_activities():
    """Restore the in-memory activities dict to its original state after each test."""
    app_module.activities.clear()
    app_module.activities.update(copy.deepcopy(_original_activities))
    yield
    app_module.activities.clear()
    app_module.activities.update(copy.deepcopy(_original_activities))


# ---------------------------------------------------------------------------
# GET /
# ---------------------------------------------------------------------------

def test_root_redirect():
    response = client.get("/")
    assert response.status_code in (301, 302, 307, 308)
    assert response.headers["location"].endswith("/static/index.html")


# ---------------------------------------------------------------------------
# GET /activities
# ---------------------------------------------------------------------------

def test_get_activities_returns_200():
    response = client.get("/activities")
    assert response.status_code == 200


def test_get_activities_returns_all_activities():
    response = client.get("/activities")
    data = response.json()
    assert len(data) == len(_original_activities)
    for name in _original_activities:
        assert name in data


def test_get_activities_contains_expected_fields():
    response = client.get("/activities")
    data = response.json()
    activity = data["Chess Club"]
    assert "description" in activity
    assert "schedule" in activity
    assert "max_participants" in activity
    assert "participants" in activity


# ---------------------------------------------------------------------------
# POST /activities/{activity_name}/signup
# ---------------------------------------------------------------------------

def test_signup_success():
    response = client.post(
        "/activities/Chess Club/signup",
        params={"email": "newstudent@mergington.edu"},
    )
    assert response.status_code == 200
    assert "newstudent@mergington.edu" in response.json()["message"]
    assert "newstudent@mergington.edu" in app_module.activities["Chess Club"]["participants"]


def test_signup_activity_not_found():
    response = client.post(
        "/activities/Nonexistent Activity/signup",
        params={"email": "student@mergington.edu"},
    )
    assert response.status_code == 404


def test_signup_already_enrolled():
    # michael@mergington.edu is already in Chess Club
    response = client.post(
        "/activities/Chess Club/signup",
        params={"email": "michael@mergington.edu"},
    )
    assert response.status_code == 400


# ---------------------------------------------------------------------------
# POST /activities/{activity_name}/unregister
# ---------------------------------------------------------------------------

def test_unregister_success():
    response = client.post(
        "/activities/Chess Club/unregister",
        params={"email": "michael@mergington.edu"},
    )
    assert response.status_code == 200
    assert "michael@mergington.edu" in response.json()["message"]
    assert "michael@mergington.edu" not in app_module.activities["Chess Club"]["participants"]


def test_unregister_activity_not_found():
    response = client.post(
        "/activities/Nonexistent Activity/unregister",
        params={"email": "student@mergington.edu"},
    )
    assert response.status_code == 404


def test_unregister_not_enrolled():
    response = client.post(
        "/activities/Chess Club/unregister",
        params={"email": "notinclub@mergington.edu"},
    )
    assert response.status_code == 400
