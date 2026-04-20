from __future__ import annotations

import json
import os
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, JSONResponse
from structlog.contextvars import bind_contextvars

from .agent import LabAgent
from .dashboard import get_dashboard_html
from .incidents import disable, enable, status
from .logging_config import configure_logging, get_logger
from .metrics import record_error, record_request, snapshot
from .middleware import CorrelationIdMiddleware
from .pii import hash_user_id, summarize_text
from .schemas import ChatRequest, ChatResponse
from .text_utils import normalize_text
from .tracing import create_trace_id_from_seed, flush_langfuse, tracing_enabled

configure_logging()
log = get_logger()
app = FastAPI(title="Day 13 Observability Lab")
app.add_middleware(CorrelationIdMiddleware)
agent = LabAgent()


def _request_latency_ms(request: Request) -> int:
    started = getattr(request.state, "request_started", None)
    if started is None:
        return 0
    try:
        import time

        return int((time.perf_counter() - started) * 1000)
    except Exception:
        return 0


def _record_failed_request(
    request: Request,
    *,
    error_type: str,
    status_code: int,
    intent: str | None = None,
    feature: str | None = None,
) -> None:
    if getattr(request.state, "metrics_recorded", False):
        return

    if request.url.path != "/chat":
        return

    resolved_intent = intent or getattr(request.state, "intent", "unknown")
    resolved_feature = feature or getattr(request.state, "feature", "unknown")
    record_request(
        latency_ms=_request_latency_ms(request),
        cost_usd=0.0,
        tokens_in=0,
        tokens_out=0,
        quality_score=0.0,
        intent=resolved_intent,
        feature=resolved_feature,
        success=False,
    )
    record_error(error_type, intent=resolved_intent)
    request.state.metrics_recorded = True


def infer_intent(feature: str, message: str) -> str:
    feature_norm = normalize_text(feature)
    if feature_norm in {"returns", "refund", "return", "hoan_tien", "hoan tien", "doi_tra", "doi tra"}:
        return "refund"
    if feature_norm in {
        "order_status",
        "tracking",
        "order",
        "don_hang",
        "don hang",
        "trang_thai_don_hang",
        "trang thai don hang",
    }:
        return "order_status"
    if feature_norm in {"shipping", "delivery", "van_chuyen", "van chuyen", "giao_hang", "giao hang"}:
        return "shipping"
    if feature_norm in {"payment", "billing", "invoice", "thanh_toan", "thanh toan", "hoa_don", "hoa don"}:
        return "payment"
    text = normalize_text(message)
    if any(keyword in text for keyword in ["refund", "return", "hoan tien", "doi tra", "tra hang", "hoan tra"]):
        return "refund"
    if any(keyword in text for keyword in ["trang thai don hang", "kiem tra don hang", "ma van don", "theo doi don", "order status"]):
        return "order_status"
    if "order" in text and ("status" in text or "track" in text):
        return "order_status"
    if any(keyword in text for keyword in ["shipping", "delivery", "van chuyen", "giao hang", "ship", "phi giao hang"]):
        return "shipping"
    if any(keyword in text for keyword in ["payment", "invoice", "charged", "thanh toan", "hoa don", "bi tru tien", "the tin dung"]):
        return "payment"
    if feature_norm in {"support", "ho_tro", "ho tro", "cskh"}:
        return "general_support"
    return "general_support"


def read_recent_logs(limit: int) -> list[dict]:
    log_path = Path(os.getenv("LOG_PATH", "data/logs.jsonl"))
    if not log_path.exists():
        return []

    lines = log_path.read_text(encoding="utf-8").splitlines()
    items: list[dict] = []
    for line in lines[-limit:]:
        if not line.strip():
            continue
        try:
            items.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return items


@app.on_event("startup")
async def startup() -> None:
    log.info(
        "app_started",
        service=os.getenv("APP_NAME", "day13-observability-lab"),
        env=os.getenv("APP_ENV", "dev"),
        payload={"tracing_enabled": tracing_enabled()},
    )


@app.on_event("shutdown")
async def shutdown() -> None:
    flush_langfuse()


@app.get("/health")
async def health() -> dict:
    return {"ok": True, "tracing_enabled": tracing_enabled(), "incidents": status()}


@app.get("/metrics")
async def metrics() -> dict:
    return snapshot()


@app.get("/logs")
async def logs(limit: int = Query(default=120, ge=1, le=1000)) -> dict:
    items = read_recent_logs(limit)
    return {"count": len(items), "items": items}


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard() -> str:
    return get_dashboard_html()


@app.exception_handler(RequestValidationError)
async def request_validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    _record_failed_request(
        request,
        error_type="HTTP_422",
        status_code=422,
        intent="unknown",
        feature="validation",
    )
    log.error(
        "request_validation_failed",
        service="api",
        error_type="RequestValidationError",
        payload={"path": request.url.path, "detail": exc.errors()},
    )
    return JSONResponse(status_code=422, content={"detail": exc.errors()})


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    error_type = f"HTTP_{exc.status_code}"
    _record_failed_request(request, error_type=error_type, status_code=exc.status_code)
    if request.url.path == "/chat":
        log.warning(
            "request_http_error",
            service="api",
            error_type=error_type,
            payload={"path": request.url.path, "detail": str(exc.detail)},
        )
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    _record_failed_request(
        request,
        error_type="HTTP_500",
        status_code=500,
    )
    log.error(
        "request_unhandled_error",
        service="api",
        error_type=type(exc).__name__,
        payload={"path": request.url.path, "detail": str(exc)},
    )
    return JSONResponse(status_code=500, content={"detail": "InternalServerError"})


@app.post("/chat", response_model=ChatResponse)
async def chat(request: Request, body: ChatRequest) -> ChatResponse:
    intent = infer_intent(body.feature, body.message)
    langfuse_trace_id = create_trace_id_from_seed(getattr(request.state, "correlation_id", None))
    request.state.intent = intent
    request.state.feature = body.feature
    bind_contextvars(
        user_id_hash=hash_user_id(body.user_id),
        session_id=body.session_id,
        feature=body.feature,
        intent=intent,
        model=agent.model,
        env=os.getenv("APP_ENV", "dev"),
    )

    log.info(
        "request_received",
        service="api",
        payload={
            "intent": intent,
            "message_preview": summarize_text(body.message),
            "domain": "ecommerce_cskh",
        },
    )
    if body.force_error_status is not None:
        raise HTTPException(
            status_code=body.force_error_status,
            detail=body.force_error_message or f"Forced HTTP {body.force_error_status} for testing",
        )

    result = agent.run(
        user_id=body.user_id,
        feature=body.feature,
        session_id=body.session_id,
        intent=intent,
        message=body.message,
        telemetry_override=body.telemetry_override,
        correlation_id=request.state.correlation_id,
        langfuse_trace_id=langfuse_trace_id,
        record_failure_metrics=False,
    )
    request.state.metrics_recorded = True
    log.info(
        "response_sent",
        service="api",
        latency_ms=result.latency_ms,
        tokens_in=result.tokens_in,
        tokens_out=result.tokens_out,
        cost_usd=result.cost_usd,
        payload={
            "intent": intent,
            "answer_preview": summarize_text(result.answer),
            "trace_id": result.trace_id,
            "trace_url": result.trace_url,
        },
    )
    return ChatResponse(
        answer=result.answer,
        correlation_id=request.state.correlation_id,
        latency_ms=result.latency_ms,
        tokens_in=result.tokens_in,
        tokens_out=result.tokens_out,
        cost_usd=result.cost_usd,
        quality_score=result.quality_score,
    )


@app.post("/incidents/{name}/enable")
async def enable_incident(name: str) -> JSONResponse:
    try:
        enable(name)
        log.warning("incident_enabled", service="control", payload={"name": name})
        return JSONResponse({"ok": True, "incidents": status()})
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/incidents/{name}/disable")
async def disable_incident(name: str) -> JSONResponse:
    try:
        disable(name)
        log.warning("incident_disabled", service="control", payload={"name": name})
        return JSONResponse({"ok": True, "incidents": status()})
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
