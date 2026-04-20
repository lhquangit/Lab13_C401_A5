from __future__ import annotations

from collections import Counter, defaultdict
from statistics import mean
from typing import Any

REQUEST_LATENCIES: list[int] = []
REQUEST_COSTS: list[float] = []
REQUEST_TOKENS_IN: list[int] = []
REQUEST_TOKENS_OUT: list[int] = []
ERRORS: Counter[str] = Counter()
INTENTS: Counter[str] = Counter()
FEATURES: Counter[str] = Counter()
INTENT_ERRORS: Counter[str] = Counter()
TOOL_LATENCIES: dict[str, list[int]] = defaultdict(list)
INTENT_LATENCIES: dict[str, list[int]] = defaultdict(list)
INTENT_COSTS: dict[str, list[float]] = defaultdict(list)
INTENT_TOKENS_IN: dict[str, list[int]] = defaultdict(list)
INTENT_TOKENS_OUT: dict[str, list[int]] = defaultdict(list)
INTENT_QUALITY_SCORES: dict[str, list[float]] = defaultdict(list)
TRAFFIC: int = 0
QUALITY_SCORES: list[float] = []
SLO_THRESHOLDS = {
    "latency_p95_ms": 3000.0,
    "error_rate_pct": 2.0,
    "daily_cost_usd": 2.5,
    "quality_score_avg": 0.75,
}


def reset() -> None:
    global TRAFFIC
    TRAFFIC = 0
    REQUEST_LATENCIES.clear()
    REQUEST_COSTS.clear()
    REQUEST_TOKENS_IN.clear()
    REQUEST_TOKENS_OUT.clear()
    QUALITY_SCORES.clear()
    ERRORS.clear()
    INTENTS.clear()
    FEATURES.clear()
    INTENT_ERRORS.clear()
    TOOL_LATENCIES.clear()
    INTENT_LATENCIES.clear()
    INTENT_COSTS.clear()
    INTENT_TOKENS_IN.clear()
    INTENT_TOKENS_OUT.clear()
    INTENT_QUALITY_SCORES.clear()


def record_request(
    latency_ms: int,
    cost_usd: float,
    tokens_in: int,
    tokens_out: int,
    quality_score: float,
    intent: str,
    feature: str,
    success: bool = True,
) -> None:
    global TRAFFIC
    TRAFFIC += 1
    REQUEST_LATENCIES.append(latency_ms)
    INTENTS[intent] += 1
    FEATURES[feature] += 1
    INTENT_LATENCIES[intent].append(latency_ms)
    if success:
        REQUEST_COSTS.append(cost_usd)
        REQUEST_TOKENS_IN.append(tokens_in)
        REQUEST_TOKENS_OUT.append(tokens_out)
        QUALITY_SCORES.append(quality_score)
        INTENT_COSTS[intent].append(cost_usd)
        INTENT_TOKENS_IN[intent].append(tokens_in)
        INTENT_TOKENS_OUT[intent].append(tokens_out)
        INTENT_QUALITY_SCORES[intent].append(quality_score)


def record_tool_latency(tool_name: str, latency_ms: int) -> None:
    TOOL_LATENCIES[tool_name].append(latency_ms)


def record_error(error_type: str, intent: str | None = None) -> None:
    ERRORS[error_type] += 1
    if intent:
        INTENT_ERRORS[intent] += 1


def percentile(values: list[int], p: int) -> float:
    if not values:
        return 0.0
    items = sorted(values)
    idx = max(0, min(len(items) - 1, round((p / 100) * len(items) + 0.5) - 1))
    return float(items[idx])


def _error_rate_pct() -> float:
    if TRAFFIC == 0:
        return 0.0
    return round((sum(ERRORS.values()) / TRAFFIC) * 100, 4)


def _tool_latency_snapshot() -> dict[str, dict[str, float | int]]:
    summary: dict[str, dict[str, float | int]] = {}
    for tool_name, latencies in TOOL_LATENCIES.items():
        summary[tool_name] = {
            "count": len(latencies),
            "avg": round(mean(latencies), 2) if latencies else 0.0,
            "p95": round(percentile(latencies, 95), 2) if latencies else 0.0,
        }
    return summary


def _intent_metrics_snapshot() -> dict[str, dict[str, float | int]]:
    intents = sorted(
        set(INTENTS.keys())
        | set(INTENT_ERRORS.keys())
        | set(INTENT_LATENCIES.keys())
        | set(INTENT_COSTS.keys())
        | set(INTENT_TOKENS_IN.keys())
        | set(INTENT_TOKENS_OUT.keys())
        | set(INTENT_QUALITY_SCORES.keys())
    )
    snapshot: dict[str, dict[str, float | int]] = {}
    for intent in intents:
        traffic = INTENTS[intent]
        errors = INTENT_ERRORS[intent]
        costs = INTENT_COSTS[intent]
        tokens_in = INTENT_TOKENS_IN[intent]
        tokens_out = INTENT_TOKENS_OUT[intent]
        qualities = INTENT_QUALITY_SCORES[intent]
        latencies = INTENT_LATENCIES[intent]
        snapshot[intent] = {
            "traffic": traffic,
            "errors": errors,
            "error_rate_pct": round((errors / traffic) * 100, 4) if traffic else 0.0,
            "avg_cost_usd": round(mean(costs), 4) if costs else 0.0,
            "total_cost_usd": round(sum(costs), 4),
            "tokens_in_total": sum(tokens_in),
            "tokens_out_total": sum(tokens_out),
            "quality_avg": round(mean(qualities), 4) if qualities else 0.0,
            "latency_p95": round(percentile(latencies, 95), 2) if latencies else 0.0,
        }
    return snapshot


def _top_business_metric(
    items: dict[str, dict[str, float | int]], key: str, lowest: bool = False
) -> dict[str, float | int | None]:
    candidates = [(intent, values[key]) for intent, values in items.items()]
    if lowest:
        candidates = [(intent, value) for intent, value in candidates if values_nonzero(value)]
    else:
        candidates = [(intent, value) for intent, value in candidates if value]
    if not candidates:
        return {"intent": None, "value": 0}
    selected = min(candidates, key=lambda item: item[1]) if lowest else max(candidates, key=lambda item: item[1])
    return {"intent": selected[0], "value": selected[1]}


def values_nonzero(value: float | int) -> bool:
    return float(value) > 0


def _business_summary(intent_metrics: dict[str, dict[str, float | int]]) -> dict[str, dict[str, float | int | None]]:
    return {
        "top_intent_by_traffic": _top_business_metric(intent_metrics, "traffic"),
        "top_intent_by_errors": _top_business_metric(intent_metrics, "errors"),
        "top_intent_by_cost": _top_business_metric(intent_metrics, "total_cost_usd"),
        "lowest_quality_intent": _top_business_metric(intent_metrics, "quality_avg", lowest=True),
    }


def _slo_status() -> dict[str, dict[str, Any]]:
    latency_p95 = percentile(REQUEST_LATENCIES, 95)
    error_rate_pct = _error_rate_pct()
    total_cost = round(sum(REQUEST_COSTS), 4)
    quality_avg = round(mean(QUALITY_SCORES), 4) if QUALITY_SCORES else 0.0
    return {
        "latency_p95_ms": {
            "objective": SLO_THRESHOLDS["latency_p95_ms"],
            "current": round(latency_p95, 2),
            "ok": latency_p95 <= SLO_THRESHOLDS["latency_p95_ms"],
        },
        "error_rate_pct": {
            "objective": SLO_THRESHOLDS["error_rate_pct"],
            "current": error_rate_pct,
            "ok": error_rate_pct <= SLO_THRESHOLDS["error_rate_pct"],
        },
        "daily_cost_usd": {
            "objective": SLO_THRESHOLDS["daily_cost_usd"],
            "current": total_cost,
            "ok": total_cost <= SLO_THRESHOLDS["daily_cost_usd"],
        },
        "quality_score_avg": {
            "objective": SLO_THRESHOLDS["quality_score_avg"],
            "current": quality_avg,
            "ok": quality_avg >= SLO_THRESHOLDS["quality_score_avg"],
        },
    }


def snapshot() -> dict:
    intent_metrics = _intent_metrics_snapshot()
    return {
        "traffic": TRAFFIC,
        "latency_p50": percentile(REQUEST_LATENCIES, 50),
        "latency_p95": percentile(REQUEST_LATENCIES, 95),
        "latency_p99": percentile(REQUEST_LATENCIES, 99),
        "avg_cost_usd": round(mean(REQUEST_COSTS), 4) if REQUEST_COSTS else 0.0,
        "total_cost_usd": round(sum(REQUEST_COSTS), 4),
        "tokens_in_total": sum(REQUEST_TOKENS_IN),
        "tokens_out_total": sum(REQUEST_TOKENS_OUT),
        "error_breakdown": dict(ERRORS),
        "error_rate_pct": _error_rate_pct(),
        "intent_breakdown": dict(INTENTS),
        "feature_breakdown": dict(FEATURES),
        "intent_metrics": intent_metrics,
        "business_summary": _business_summary(intent_metrics),
        "tool_latency_ms": _tool_latency_snapshot(),
        "quality_avg": round(mean(QUALITY_SCORES), 4) if QUALITY_SCORES else 0.0,
        "slo_status": _slo_status(),
    }
