import pytest

from fastapi.testclient import TestClient


def test_access_without_token(client: TestClient):
    response = client.get("/predictions")

    assert response.status_code == 401


def test_access_other_user_resource_bola(
    client: TestClient, normal_user_headers: dict, admin_user_headers: dict
):
    create_pred_response = client.post(
        "/predictions/predict",
        json={"text": "Predição criada pelo Admin para teste de BOLA"},
        headers=admin_user_headers,
    )
    assert create_pred_response.status_code == 201

    admin_prediction_id = create_pred_response.json()["prediction_id"]

    response = client.get(
        f"/predictions/{admin_prediction_id}", headers=normal_user_headers
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Access forbidden."


def test_reject_extra_fields_in_request_body(
    client: TestClient, normal_user_headers: dict
):
    payload = {
        "text": "Preciso de ajuda com para cancelar a assinatura",
        "role": "admin",
    }

    response = client.post(
        "/predictions/predict",
        json=payload,
        headers=normal_user_headers,
    )

    assert response.status_code == 422

    # Garante que o 422 foi causado pelo campo extra, e não por outro erro de validação.
    error = response.json()["detail"][0]
    assert error["type"] == "extra_forbidden"
    assert error["loc"] == ["body", "role"]


@pytest.mark.usefixtures("reset_rate_limit")
def test_rate_limit_on_auth_token(client: TestClient):
    credentials = {"username": "janedoe", "password": "senha-errada"}

    for _ in range(10):
        response = client.post("/auth/token", data=credentials)
        assert response.status_code == 401

    response = client.post("/auth/token", data=credentials)

    assert response.status_code == 429
