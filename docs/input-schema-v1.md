# Input Schema V1 (Lab 13 Observability)

This document defines the shared request contract for `POST /chat` so all team members can build consistent test cases and compare monitoring signals.

## 1. Endpoint Contract

- Method: `POST`
- Path: `/chat`
- Content-Type: `application/json`
- Optional header: `x-request-id: req-<8_hex>`
  - If missing, middleware should generate one.

## 2. JSON Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "ChatRequestV1",
  "type": "object",
  "required": ["user_id", "session_id", "feature", "message"],
  "additionalProperties": false,
  "properties": {
    "user_id": {
      "type": "string",
      "minLength": 2,
      "maxLength": 64,
      "pattern": "^[a-zA-Z0-9_-]+$",
      "examples": ["u01", "teamA_user_1"]
    },
    "session_id": {
      "type": "string",
      "minLength": 2,
      "maxLength": 64,
      "pattern": "^[a-zA-Z0-9_-]+$",
      "examples": ["s01", "demo_session_01"]
    },
    "feature": {
      "type": "string",
      "minLength": 2,
      "maxLength": 32,
      "examples": ["qa", "summary"]
    },
    "message": {
      "type": "string",
      "minLength": 1,
      "maxLength": 2000
    },
    "telemetry_override": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "latency_ms": { "type": "integer", "minimum": 0, "maximum": 60000 },
        "rag_latency_ms": { "type": "integer", "minimum": 0, "maximum": 60000 },
        "llm_latency_ms": { "type": "integer", "minimum": 0, "maximum": 60000 },
        "tokens_in": { "type": "integer", "minimum": 0 },
        "tokens_out": { "type": "integer", "minimum": 0 },
        "cost_usd": { "type": "number", "minimum": 0 },
        "quality_score": { "type": "number", "minimum": 0, "maximum": 1 }
      }
    },
    "force_error_status": {
      "type": "integer",
      "minimum": 400,
      "maximum": 599
    },
    "force_error_message": {
      "type": "string",
      "maxLength": 200
    }
  }
}
```

## 3. Validation Notes

- `message` must not be empty.
- Missing any required field should return HTTP `422`.
- Unknown fields should be rejected (because `additionalProperties=false` in this contract).
- `telemetry_override` is optional and only used for lab/demo purposes to push chosen latency, tokens, cost, or quality values into dashboard metrics.
- `force_error_status` is optional and can be used to force a failed request such as `429` or `500` to verify `Error Rate` and logs.
- Observability expectation:
  - Every accepted request should emit logs with `correlation_id`.
  - PII in log payload must be redacted.
  - Trace should include request flow and tool spans when tracing is enabled.

## 3.1 Example Request For Dashboard Testing

```json
{
  "user_id": "u_demo_01",
  "session_id": "s_demo_01",
  "feature": "order_status",
  "message": "Tôi muốn kiểm tra trạng thái đơn hàng.",
  "telemetry_override": {
    "latency_ms": 3200,
    "rag_latency_ms": 1800,
    "llm_latency_ms": 900,
    "tokens_in": 240,
    "tokens_out": 850,
    "cost_usd": 0.0215
  }
}
```

Ví dụ tạo lỗi để kiểm tra `Error Rate`:

```json
{
  "user_id": "u_demo_02",
  "session_id": "s_demo_02",
  "feature": "payment",
  "message": "Tôi muốn kiểm tra thanh toán.",
  "force_error_status": 429,
  "force_error_message": "Rate limit test"
}
```

## 4. Shared Test Case File

Use [`data/test_cases.jsonl`](/Users/quanliver/Projects/AI_Vin_Learner/Lab13-Observability_v1/data/test_cases.jsonl) as the team baseline test set.

Each line contains:
- `case_id`: stable identifier
- `category`: normal, pii, validation, incident
- `incident`: optional toggle to apply before running case
- `headers`: request headers
- `payload`: JSON body for `/chat`
- `expected`: minimum expected outcome

## 5. Suggested Run Flow

1. Start app: `uvicorn app.main:app --reload`
2. Run baseline traffic with normal + pii cases
3. Run incident cases (`rag_slow`, `tool_fail`, `cost_spike`)
4. Verify:
   - `python scripts/validate_logs.py`
   - `GET /metrics`
   - trace list and waterfall in Langfuse
