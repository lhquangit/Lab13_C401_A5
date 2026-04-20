import argparse
import concurrent.futures
import json
import time
from pathlib import Path

import httpx

BASE_URL = "http://127.0.0.1:8000"
QUERIES = Path("data/sample_queries.jsonl")


def send_request(client: httpx.Client, payload: dict, label: str = "payload") -> None:
    try:
        start = time.perf_counter()
        r = client.post(f"{BASE_URL}/chat", json=payload)
        latency = (time.perf_counter() - start) * 1000
        print(f"[{r.status_code}] {r.json().get('correlation_id')} | {label} | {payload['feature']} | {latency:.1f}ms")
    except Exception as e:
        print(f"Error: {e}")


def load_payloads(path: Path) -> list[tuple[str, dict]]:
    payloads: list[tuple[str, dict]] = []
    lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    for idx, line in enumerate(lines, start=1):
        item = json.loads(line)
        if "payload" in item:
            payloads.append((item.get("case_id", f"case_{idx}"), item["payload"]))
        else:
            payloads.append((f"sample_{idx}", item))
    return payloads


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--concurrency", type=int, default=1, help="Number of concurrent requests")
    parser.add_argument("--input", type=Path, default=QUERIES, help="Path to JSONL payloads or case definitions")
    args = parser.parse_args()

    cases = load_payloads(args.input)

    with httpx.Client(timeout=30.0) as client:
        if args.concurrency > 1:
            with concurrent.futures.ThreadPoolExecutor(max_workers=args.concurrency) as executor:
                futures = [executor.submit(send_request, client, payload, label) for label, payload in cases]
                concurrent.futures.wait(futures)
        else:
            for label, payload in cases:
                send_request(client, payload, label)


if __name__ == "__main__":
    main()
