from fastapi.testclient import TestClient

from app import metrics
from app.main import app


client = TestClient(app)


def setup_function() -> None:
    metrics.reset()


def test_chat_telemetry_override_updates_metrics_snapshot() -> None:
    response = client.post(
        "/chat",
        json={
            "user_id": "u_override_01",
            "session_id": "s_override_01",
            "feature": "order_status",
            "message": "Tôi muốn kiểm tra trạng thái đơn hàng.",
            "telemetry_override": {
                "latency_ms": 1200,
                "rag_latency_ms": 700,
                "llm_latency_ms": 300,
                "tokens_in": 210,
                "tokens_out": 640,
                "cost_usd": 0.025,
            },
        },
    )

    assert response.status_code == 200
    body = response.json()
    snapshot = metrics.snapshot()

    assert body["latency_ms"] == 1200
    assert body["tokens_in"] == 210
    assert body["tokens_out"] == 640
    assert body["cost_usd"] == 0.025
    assert snapshot["latency_p95"] == 1200.0
    assert snapshot["tokens_in_total"] == 210
    assert snapshot["tokens_out_total"] == 640
    assert snapshot["total_cost_usd"] == 0.025
    assert snapshot["tool_latency_ms"]["rag.retrieve"]["count"] == 1
    assert snapshot["tool_latency_ms"]["llm.generate"]["count"] == 1


def test_error_rate_updates_for_forced_http_error() -> None:
    response = client.post(
        "/chat",
        json={
            "user_id": "u_error_01",
            "session_id": "s_error_01",
            "feature": "payment",
            "message": "Tôi muốn kiểm tra thanh toán.",
            "force_error_status": 429,
            "force_error_message": "Rate limit test",
        },
    )

    assert response.status_code == 429
    snapshot = metrics.snapshot()

    assert snapshot["traffic"] == 1
    assert snapshot["error_rate_pct"] == 100.0
    assert snapshot["error_breakdown"]["HTTP_429"] == 1


def test_error_rate_updates_for_validation_error() -> None:
    response = client.post(
        "/chat",
        json={
            "user_id": "u_error_02",
            "session_id": "s_error_02",
            "feature": "payment",
        },
    )

    assert response.status_code == 422
    snapshot = metrics.snapshot()

    assert snapshot["traffic"] == 1
    assert snapshot["error_rate_pct"] == 100.0
    assert snapshot["error_breakdown"]["HTTP_422"] == 1
    assert snapshot["feature_breakdown"]["validation"] == 1
