from app import metrics


def setup_function() -> None:
    metrics.reset()


def test_percentile_basic() -> None:
    assert metrics.percentile([100, 200, 300, 400], 50) >= 100


def test_snapshot_includes_error_rate_and_intent_breakdown() -> None:
    metrics.record_request(
        latency_ms=120,
        cost_usd=0.001,
        tokens_in=100,
        tokens_out=180,
        quality_score=0.8,
        intent="refund",
        feature="returns",
        success=True,
    )
    metrics.record_request(
        latency_ms=900,
        cost_usd=0.0,
        tokens_in=0,
        tokens_out=0,
        quality_score=0.0,
        intent="payment",
        feature="payment",
        success=False,
    )
    metrics.record_error("RuntimeError", intent="payment")

    snapshot = metrics.snapshot()

    assert snapshot["traffic"] == 2
    assert snapshot["error_rate_pct"] == 50.0
    assert snapshot["intent_breakdown"]["refund"] == 1
    assert snapshot["intent_breakdown"]["payment"] == 1
    assert snapshot["feature_breakdown"]["returns"] == 1
    assert snapshot["feature_breakdown"]["payment"] == 1
    assert snapshot["intent_metrics"]["refund"]["traffic"] == 1
    assert snapshot["intent_metrics"]["payment"]["errors"] == 1
    assert snapshot["intent_metrics"]["payment"]["error_rate_pct"] == 100.0


def test_snapshot_includes_business_summary() -> None:
    metrics.record_request(
        latency_ms=180,
        cost_usd=0.004,
        tokens_in=120,
        tokens_out=220,
        quality_score=0.82,
        intent="refund",
        feature="returns",
        success=True,
    )
    metrics.record_request(
        latency_ms=400,
        cost_usd=0.009,
        tokens_in=210,
        tokens_out=480,
        quality_score=0.61,
        intent="payment",
        feature="payment",
        success=True,
    )
    metrics.record_request(
        latency_ms=520,
        cost_usd=0.0,
        tokens_in=0,
        tokens_out=0,
        quality_score=0.0,
        intent="payment",
        feature="payment",
        success=False,
    )
    metrics.record_error("RuntimeError", intent="payment")

    snapshot = metrics.snapshot()

    assert snapshot["business_summary"]["top_intent_by_traffic"]["intent"] == "payment"
    assert snapshot["business_summary"]["top_intent_by_errors"]["intent"] == "payment"
    assert snapshot["business_summary"]["top_intent_by_cost"]["intent"] == "payment"
    assert snapshot["business_summary"]["lowest_quality_intent"]["intent"] == "payment"


def test_snapshot_includes_tool_latency_breakdown() -> None:
    metrics.record_tool_latency("rag.retrieve", 200)
    metrics.record_tool_latency("rag.retrieve", 400)
    metrics.record_tool_latency("llm.generate", 150)

    snapshot = metrics.snapshot()

    assert snapshot["tool_latency_ms"]["rag.retrieve"]["count"] == 2
    assert snapshot["tool_latency_ms"]["rag.retrieve"]["p95"] >= 200
    assert snapshot["tool_latency_ms"]["llm.generate"]["count"] == 1
