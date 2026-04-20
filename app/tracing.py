from __future__ import annotations

import os
from contextlib import nullcontext
from typing import Any, Callable, ContextManager

from dotenv import load_dotenv

load_dotenv()

if os.getenv("LANGFUSE_HOST") and not os.getenv("LANGFUSE_BASE_URL"):
    os.environ["LANGFUSE_BASE_URL"] = os.getenv("LANGFUSE_HOST", "")

if os.getenv("APP_ENV") and not os.getenv("LANGFUSE_TRACING_ENVIRONMENT"):
    os.environ["LANGFUSE_TRACING_ENVIRONMENT"] = os.getenv("APP_ENV", "dev")

if os.getenv("APP_VERSION") and not os.getenv("LANGFUSE_RELEASE"):
    os.environ["LANGFUSE_RELEASE"] = os.getenv("APP_VERSION", "")

try:
    from langfuse import get_client, observe, propagate_attributes
except Exception:  # pragma: no cover
    def observe(*args: Any, **kwargs: Any):
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            return func

        return decorator

    def propagate_attributes(**kwargs: Any):
        return nullcontext()

    class _DummyLangfuseClient:
        def create_trace_id(self, seed: str | None = None) -> str | None:
            return None

        def get_current_trace_id(self) -> str | None:
            return None

        def get_trace_url(self, trace_id: str | None = None) -> str | None:
            return None

        def update_current_span(self, **kwargs: Any) -> None:
            return None

        def update_current_generation(self, **kwargs: Any) -> None:
            return None

        def flush(self) -> None:
            return None

    _DUMMY_CLIENT = _DummyLangfuseClient()

    def get_client() -> _DummyLangfuseClient:
        return _DUMMY_CLIENT


def get_langfuse_client():
    return get_client()


def observe_step(name: str, *, as_type: str = "span"):
    return observe(name=name, as_type=as_type, capture_input=False, capture_output=False)


def tracing_enabled() -> bool:
    return bool(os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY"))


def create_trace_id_from_seed(seed: str | None) -> str | None:
    if not tracing_enabled() or not seed:
        return None
    try:
        return get_langfuse_client().create_trace_id(seed=seed)
    except Exception:
        return None


def trace_attributes(
    *,
    trace_name: str,
    user_id: str,
    session_id: str,
    tags: list[str] | None = None,
    metadata: dict[str, str] | None = None,
) -> ContextManager[Any]:
    if not tracing_enabled():
        return nullcontext()

    safe_metadata = {k: str(v)[:200] for k, v in (metadata or {}).items()}
    return propagate_attributes(
        trace_name=trace_name,
        user_id=user_id,
        session_id=session_id,
        tags=tags or [],
        metadata=safe_metadata,
    )


def current_trace_info() -> tuple[str | None, str | None]:
    if not tracing_enabled():
        return None, None

    try:
        client = get_langfuse_client()
        trace_id = client.get_current_trace_id()
        trace_url = client.get_trace_url(trace_id=trace_id) if trace_id else None
        return trace_id, trace_url
    except Exception:
        return None, None


def flush_langfuse() -> None:
    if not tracing_enabled():
        return
    try:
        get_langfuse_client().flush()
    except Exception:
        return
