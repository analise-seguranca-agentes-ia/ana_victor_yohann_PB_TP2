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

    admin_predictions_response = client.get("/predictions", headers=admin_user_headers)
    assert admin_predictions_response.status_code == 200

    admin_predictions = admin_predictions_response.json()
    admin_prediction_id = admin_predictions[0]["prediction_id"]

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
