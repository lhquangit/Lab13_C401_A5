"""inject_incident.py -- Inject and verify incident scenarios for the CSKH e-commerce chatbot.

Usage:
    python scripts/inject_incident.py --scenario rag_slow
    python scripts/inject_incident.py --scenario tool_fail
    python scripts/inject_incident.py --scenario cost_spike
    python scripts/inject_incident.py --scenario rag_slow --disable
    python scripts/inject_incident.py --list
    python scripts/inject_incident.py --status
"""
from __future__ import annotations

import argparse
import io
import json
import sys
import time

# Ensure UTF-8 output on Windows so emojis / unicode display correctly
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import httpx

BASE_URL = "http://127.0.0.1:8000"

# ── Scenario catalogue ────────────────────────────────────────────────────────
SCENARIOS: dict[str, dict] = {
    "rag_slow": {
        "description": "RAG retrieval latency spike — P95 climbs above 5 000 ms.",
        "alert": "high_latency_p95",
        "severity": "P2",
        "business_impact": "Customers wait too long for refund / order-status answers.",
        "expected_log_event": "tool_call_succeeded (rag.retrieve) with high latency_ms",
        "verify_metric": "latency_p95",
        "verify_threshold": 5000,
        "runbook": "docs/incident_runbook.md#case-1-rag-slow",
        "sample_queries": [
            {"feature": "returns", "message": "Tôi muốn hoàn tiền đơn hàng #12345"},
            {"feature": "order_status", "message": "Đơn hàng của tôi đang ở đâu?"},
            {"feature": "shipping", "message": "Phí vận chuyển bao nhiêu?"},
        ],
    },
    "tool_fail": {
        "description": "Tool / retrieval failure causing 500 errors — error_rate_pct > 5 %.",
        "alert": "high_error_rate",
        "severity": "P1",
        "business_impact": "Chatbot fails to answer refund, shipping, or payment requests.",
        "expected_log_event": "tool_call_failed + request_failed with error_type=RuntimeError",
        "verify_metric": "error_rate_pct",
        "verify_threshold": 5,
        "runbook": "docs/incident_runbook.md#case-2-tool-fail",
        "sample_queries": [
            {"feature": "payment", "message": "Tôi bị trừ tiền nhưng đơn hàng chưa xác nhận"},
            {"feature": "returns", "message": "Hoàn tiền bị từ chối, tôi phải làm gì?"},
            {"feature": "support", "message": "Tôi cần hỗ trợ gấp!"},
        ],
    },
    "cost_spike": {
        "description": "LLM token output spike — hourly cost rises above 2× baseline.",
        "alert": "cost_budget_spike",
        "severity": "P2",
        "business_impact": "Support-bot operating cost spikes above the daily budget.",
        "expected_log_event": "tool_call_succeeded (llm.generate) with high tokens_out",
        "verify_metric": "total_cost_usd",
        "verify_threshold": 2.5,
        "runbook": "docs/incident_runbook.md#case-3-cost-spike",
        "sample_queries": [
            {"feature": "payment", "message": "Giải thích chi tiết chính sách hoàn tiền"},
            {"feature": "shipping", "message": "Liệt kê tất cả tùy chọn giao hàng và chi phí"},
            {"feature": "returns", "message": "Quy trình đổi trả hàng như thế nào?"},
        ],
    },
}


# ── HTTP helpers ──────────────────────────────────────────────────────────────

def _post(path: str, payload: dict | None = None) -> dict:
    try:
        r = httpx.post(f"{BASE_URL}{path}", json=payload, timeout=10.0)
        r.raise_for_status()
        return r.json()
    except httpx.HTTPError as exc:
        print(f"[ERROR] HTTP request failed: {exc}", file=sys.stderr)
        sys.exit(1)


def _get(path: str) -> dict:
    try:
        r = httpx.get(f"{BASE_URL}{path}", timeout=10.0)
        r.raise_for_status()
        return r.json()
    except httpx.HTTPError as exc:
        print(f"[ERROR] HTTP request failed: {exc}", file=sys.stderr)
        sys.exit(1)


# ── Display helpers ───────────────────────────────────────────────────────────

def _banner(text: str) -> None:
    bar = "=" * (len(text) + 4)
    print(f"\n+{bar}+")
    print(f"|  {text}  |")
    print(f"+{bar}+")


def _print_scenario_info(name: str) -> None:
    info = SCENARIOS[name]
    print(f"\n  [Scenario]    {name}")
    print(f"  [Alert]       {info['alert']}  [{info['severity']}]")
    print(f"  [Impact]      {info['business_impact']}")
    print(f"  [Runbook]     {info['runbook']}")
    print(f"  [Description] {info['description']}")


# ── Core actions ──────────────────────────────────────────────────────────────

def list_scenarios() -> None:
    _banner("Available Incident Scenarios")
    for name, info in SCENARIOS.items():
        print(f"\n  scenario : {name}")
        print(f"    severity : {info['severity']}")
        print(f"    alert    : {info['alert']}")
        print(f"    impact   : {info['business_impact']}")
        print(f"    runbook  : {info['runbook']}")


def show_status() -> None:
    _banner("Current Incident State")
    health = _get("/health")
    incidents = health.get("incidents", {})
    metrics = _get("/metrics")

    for name, enabled in incidents.items():
        status_label = "ON " if enabled else "OFF"
        print(f"  [{status_label:3s}]  {name}")

    print("\n  -- Live Metrics --")
    slo = metrics.get("slo_status", {})
    for key, item in slo.items():
        ok_label = "OK " if item.get("ok") else "ERR"
        print(f"  [{ok_label}]  {key:25s}  current={item['current']}  target={item['objective']}")


def enable_incident(name: str) -> None:
    _banner(f"Enabling Incident: {name}")
    _print_scenario_info(name)

    data = _post(f"/incidents/{name}/enable")
    print(f"\n  [ON]  Incident {name!r} is now ACTIVE")
    print(f"  Incidents: {json.dumps(data.get('incidents', {}), indent=4)}")

    info = SCENARIOS[name]
    print(f"\n  Sending {len(info['sample_queries'])} sample queries to trigger alert...")
    _send_sample_queries(info["sample_queries"])

    # Brief wait then verify
    time.sleep(2)
    _verify_alert_condition(name)


def disable_incident(name: str) -> None:
    _banner(f"Disabling Incident: {name}")
    data = _post(f"/incidents/{name}/disable")
    print(f"\n  [OFF] Incident {name!r} is now INACTIVE")
    print(f"  Incidents: {json.dumps(data.get('incidents', {}), indent=4)}")


# ── Sample query sender ───────────────────────────────────────────────────────

def _send_sample_queries(queries: list[dict]) -> None:
    for i, q in enumerate(queries, 1):
        payload = {
            "user_id": f"inject-user-{i:03d}",
            "session_id": f"inject-session-{i:03d}",
            "feature": q["feature"],
            "message": q["message"],
        }
        try:
            r = httpx.post(f"{BASE_URL}/chat", json=payload, timeout=15.0)
            status_label = "OK " if r.status_code == 200 else f"ERR HTTP {r.status_code}"
            answer_preview = ""
            if r.status_code == 200:
                body = r.json()
                answer_preview = (body.get("answer", "")[:60] + "...") if body.get("answer") else ""
            print(f"    [{status_label}]  [{q['feature']}] {q['message'][:50]}")
            if answer_preview:
                print(f"           -> {answer_preview}")
        except httpx.HTTPError as exc:
            print(f"    [ERR] Request failed: {exc}")


# ── Alert verification ────────────────────────────────────────────────────────

def _verify_alert_condition(name: str) -> None:
    info = SCENARIOS[name]
    metrics = _get("/metrics")
    slo = metrics.get("slo_status", {})

    print(f"\n  [Verify] Alert: {info['alert']} ({info['severity']})")
    print(f"  Condition  : {_alert_condition_label(name)}")

    # Map metric name to SLO key
    slo_key_map = {
        "latency_p95": "latency_p95_ms",
        "error_rate_pct": "error_rate_pct",
        "total_cost_usd": "daily_cost_usd",
    }
    metric_key = info["verify_metric"]
    slo_key = slo_key_map.get(metric_key, metric_key)
    slo_entry = slo.get(slo_key, {})

    current = slo_entry.get("current", 0)
    objective = slo_entry.get("objective", 0)
    ok = slo_entry.get("ok", True)

    status_label = "OK" if ok else "BREACHED"
    print(f"  SLO status : [{status_label}]  (current={current}, target={objective})")
    print(f"  Expected   : {info['expected_log_event']}")
    print(f"\n  Open dashboard -> http://127.0.0.1:8000/dashboard")
    print(f"  Follow runbook -> {info['runbook']}")


def _alert_condition_label(name: str) -> str:
    labels = {
        "rag_slow": "latency_p95_ms > 5000 ms for 30 min",
        "tool_fail": "error_rate_pct > 5 % for 5 min",
        "cost_spike": "hourly_cost_usd > 2× baseline for 15 min",
    }
    return labels.get(name, "n/a")


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Inject and verify incident scenarios for the CSKH e-commerce chatbot."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--scenario",
        choices=list(SCENARIOS.keys()),
        help="Incident scenario to inject.",
    )
    group.add_argument("--list", action="store_true", help="List all available scenarios.")
    group.add_argument("--status", action="store_true", help="Show current incident and SLO state.")

    parser.add_argument(
        "--disable",
        action="store_true",
        help="Disable the specified scenario (default: enable).",
    )
    args = parser.parse_args()

    if args.list:
        list_scenarios()
        return

    if args.status:
        show_status()
        return

    if args.disable:
        disable_incident(args.scenario)
    else:
        enable_incident(args.scenario)


if __name__ == "__main__":
    main()
