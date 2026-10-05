import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "fastapi"))

import sqlite_database

# Os testes usam um banco temporário para não alterar o fastapi/database.db
# versionado. O caminho precisa ser trocado antes de importar a aplicação,
# pois o database.py cria a engine e popula o banco no momento do import.
TEST_DB_DIR = Path(tempfile.mkdtemp())
sqlite_database.DATABASE_PATH = TEST_DB_DIR / "test_database.db"

import pytest
from database import engine
from limiter import limiter
from main import app
from sqlite_database import init_and_seed_db

from fastapi.testclient import TestClient


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    init_and_seed_db()
    yield
    engine.dispose()
    shutil.rmtree(TEST_DB_DIR, ignore_errors=True)


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def reset_rate_limit():
    limiter.reset()
    yield
    limiter.reset()


# Os tokens são gerados uma única vez por sessão para não consumir o limite
# de 10 requisições/minuto do /auth/token a cada teste.
@pytest.fixture(scope="session")
def normal_user_token(client: TestClient) -> str:
    response = client.post(
        "/auth/token",
        data={"username": "janedoe", "password": "janedoe123"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture(scope="session")
def admin_user_token(client: TestClient) -> str:
    response = client.post(
        "/auth/token",
        data={"username": "johndoe", "password": "johndoe123"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture(scope="session")
def normal_user_headers(normal_user_token: str) -> dict:
    return {"Authorization": f"Bearer {normal_user_token}"}


@pytest.fixture(scope="session")
def admin_user_headers(admin_user_token: str) -> dict:
    return {"Authorization": f"Bearer {admin_user_token}"}
