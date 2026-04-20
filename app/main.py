from __future__ import annotations

import json
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse
from structlog.contextvars import bind_contextvars

from .agent import LabAgent
from .dashboard import get_dashboard_html
from .incidents import disable, enable, status
from .logging_config import configure_logging, get_logger
from .metrics import record_error, snapshot
from .middleware import CorrelationIdMiddleware
from .pii import hash_user_id, summarize_text
from .schemas import ChatRequest, ChatResponse
from .text_utils import normalize_text
from .tracing import tracing_enabled

load_dotenv()

configure_logging()
log = get_logger()
app = FastAPI(title="Day 13 Observability Lab")
app.add_middleware(CorrelationIdMiddleware)
agent = LabAgent()


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
    if feature_norm in {"support", "ho_tro", "ho tro", "cskh"}:
        return "general_support"

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


@app.post("/chat", response_model=ChatResponse)
async def chat(request: Request, body: ChatRequest) -> ChatResponse:
    intent = infer_intent(body.feature, body.message)
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
    try:
        result = agent.run(
            user_id=body.user_id,
            feature=body.feature,
            session_id=body.session_id,
            intent=intent,
            message=body.message,
        )
        log.info(
            "response_sent",
            service="api",
            latency_ms=result.latency_ms,
            tokens_in=result.tokens_in,
            tokens_out=result.tokens_out,
            cost_usd=result.cost_usd,
            payload={"intent": intent, "answer_preview": summarize_text(result.answer)},
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
    except Exception as exc:  # pragma: no cover
        error_type = type(exc).__name__
        record_error(error_type, intent=intent)
        log.error(
            "request_failed",
            service="api",
            error_type=error_type,
            payload={
                "intent": intent,
                "detail": str(exc),
                "message_preview": summarize_text(body.message),
            },
        )
        raise HTTPException(status_code=500, detail=error_type) from exc


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
