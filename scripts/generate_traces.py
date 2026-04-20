from __future__ import annotations

import argparse
import concurrent.futures
import copy
import itertools
import json
import uuid
from pathlib import Path

import httpx

BASE_URL = "http://127.0.0.1:8000"
DEFAULT_INPUT = Path("data/sample_queries.jsonl")


def load_payloads(path: Path, *, include_errors: bool) -> list[dict]:
    payloads: list[dict] = []
    lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    for line in lines:
        item = json.loads(line)
        payload = item.get("payload", item)
        if not include_errors and payload.get("force_error_status") is not None:
            continue
        payloads.append(payload)
    return payloads


def make_request_payload(base_payload: dict, sequence: int) -> dict:
    payload = copy.deepcopy(base_payload)
    suffix = f"t{sequence:03d}"

    if "user_id" in payload and payload["user_id"]:
        payload["user_id"] = f"{payload['user_id']}_{suffix}"
    else:
        payload["user_id"] = f"user_{suffix}"

    if "session_id" in payload and payload["session_id"]:
        payload["session_id"] = f"{payload['session_id']}_{suffix}"
    else:
        payload["session_id"] = f"session_{suffix}"

    return payload


def request_headers() -> dict[str, str]:
    return {
        "Content-Type": "application/json",
        "x-request-id": f"req-{uuid.uuid4().hex[:8]}",
    }


def send_request(client: httpx.Client, payload: dict, sequence: int) -> tuple[int, str | None]:
    response = client.post(f"{BASE_URL}/chat", json=payload, headers=request_headers())
    correlation_id = None
    try:
        correlation_id = response.json().get("correlation_id")
    except Exception:
        correlation_id = None

    label = payload.get("feature", "unknown")
    print(f"[{response.status_code}] trace_{sequence:03d} | {label} | correlation_id={correlation_id}")
    return response.status_code, correlation_id


def check_health() -> None:
    response = httpx.get(f"{BASE_URL}/health", timeout=10.0)
    response.raise_for_status()
    data = response.json()
    if not data.get("ok"):
        raise RuntimeError("Application health check failed.")
    if not data.get("tracing_enabled"):
        raise RuntimeError("Tracing is disabled. Check Langfuse env vars and restart the app.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate successful /chat requests to create Langfuse traces."
    )
    parser.add_argument("--count", type=int, default=10, help="Number of requests/traces to create")
    parser.add_argument("--concurrency", type=int, default=1, help="Number of concurrent requests")
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT,
        help="Path to JSONL payloads or test case definitions",
    )
    parser.add_argument(
        "--include-errors",
        action="store_true",
        help="Include payloads that intentionally force HTTP errors",
    )
    args = parser.parse_args()

    check_health()

    base_payloads = load_payloads(args.input, include_errors=args.include_errors)
    if not base_payloads:
        raise RuntimeError("No payloads available to generate traces.")

    request_payloads = [
        make_request_payload(base_payload, idx)
        for idx, base_payload in zip(range(1, args.count + 1), itertools.cycle(base_payloads))
    ]

    success_count = 0
    with httpx.Client(timeout=90.0) as client:
        if args.concurrency > 1:
            with concurrent.futures.ThreadPoolExecutor(max_workers=args.concurrency) as executor:
                futures = [
                    executor.submit(send_request, client, payload, idx)
                    for idx, payload in enumerate(request_payloads, start=1)
                ]
                for future in concurrent.futures.as_completed(futures):
                    status_code, _ = future.result()
                    if 200 <= status_code < 300:
                        success_count += 1
        else:
            for idx, payload in enumerate(request_payloads, start=1):
                status_code, _ = send_request(client, payload, idx)
                if 200 <= status_code < 300:
                    success_count += 1

    print(
        f"\nGenerated requests: {len(request_payloads)} | Successful responses: {success_count} | "
        f"Expected Langfuse traces: at least {success_count}"
    )


if __name__ == "__main__":
    main()
