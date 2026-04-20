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
    }
  }
}
```

## 3. Validation Notes

- `message` must not be empty.
- Missing any required field should return HTTP `422`.
- Unknown fields should be rejected (because `additionalProperties=false` in this contract).
- Observability expectation:
  - Every accepted request should emit logs with `correlation_id`.
  - PII in log payload must be redacted.
  - Trace should include request flow and tool spans when tracing is enabled.

## 4. Shared Test Case File

Use [`data/test_cases.jsonl`](/Users/quanliver/Projects/AI_Vin_Learner/Lab13-Observability/data/test_cases.jsonl) as the team baseline test set.

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
