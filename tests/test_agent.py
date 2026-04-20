import pytest

from app import metrics
from app.agent import LabAgent
from app.mock_llm import FakeResponse, FakeUsage


def setup_function() -> None:
    metrics.reset()


def test_agent_run_records_tool_metrics(monkeypatch: pytest.MonkeyPatch) -> None:
    agent = LabAgent()

    monkeypatch.setattr("app.agent.retrieve", lambda message: ["Refunds are available within 7 days."])
    monkeypatch.setattr(
        agent.llm,
        "generate",
        lambda prompt: FakeResponse(
            text="You can request a refund within 7 days with proof of purchase.",
            usage=FakeUsage(input_tokens=60, output_tokens=90),
            model=agent.model,
        ),
    )

    result = agent.run(
        user_id="cust_001",
        feature="returns",
        session_id="sess_001",
        intent="refund",
        message="I need a refund for my order.",
    )

    snapshot = metrics.snapshot()

    assert result.tokens_in == 60
    assert snapshot["traffic"] == 1
    assert snapshot["intent_breakdown"]["refund"] == 1
    assert snapshot["tool_latency_ms"]["rag.retrieve"]["count"] == 1
    assert snapshot["tool_latency_ms"]["llm.generate"]["count"] == 1


def test_agent_run_records_failed_request(monkeypatch: pytest.MonkeyPatch) -> None:
    agent = LabAgent()

    def raise_timeout(message: str) -> list[str]:
        raise RuntimeError("Vector store timeout")

    monkeypatch.setattr("app.agent.retrieve", raise_timeout)

    with pytest.raises(RuntimeError):
        agent.run(
            user_id="cust_002",
            feature="returns",
            session_id="sess_002",
            intent="refund",
            message="My order arrived damaged.",
        )

    snapshot = metrics.snapshot()

    assert snapshot["traffic"] == 1
    assert snapshot["intent_breakdown"]["refund"] == 1
    assert snapshot["tool_latency_ms"]["rag.retrieve"]["count"] == 1
