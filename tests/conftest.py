import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "fastapi"))

import pytest
from main import app
from sqlite_database import init_and_seed_db
from fastapi.testclient import TestClient

@pytest.fixture(scope="session", autouse=True)
def setup_database():
    init_and_seed_db()


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def normal_user_token(client: TestClient) -> str:
    response = client.post(
        "/auth/token",
        data={"username": "janedoe", "password": "janedoe123"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture
def admin_user_token(client: TestClient) -> str:
    response = client.post(
        "/auth/token",
        data={"username": "johndoe", "password": "johndoe123"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture
def normal_user_headers(normal_user_token: str) -> dict:
    return {"Authorization": f"Bearer {normal_user_token}"}


@pytest.fixture
def admin_user_headers(admin_user_token: str) -> dict:
    return {"Authorization": f"Bearer {admin_user_token}"}
