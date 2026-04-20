from __future__ import annotations

import os
import time
from dataclasses import dataclass

from structlog.contextvars import bind_contextvars

from . import metrics
from .incidents import status as incident_status
from .logging_config import get_logger
from .mock_llm import FakeLLM, FakeResponse
from .mock_rag import retrieve
from .pii import hash_user_id, summarize_text
from .schemas import TelemetryOverride
from .tracing import current_trace_info, get_langfuse_client, observe, observe_step, trace_attributes

log = get_logger()


@dataclass
class AgentResult:
    answer: str
    latency_ms: int
    tokens_in: int
    tokens_out: int
    cost_usd: float
    quality_score: float
    trace_id: str | None = None
    trace_url: str | None = None


class LabAgent:
    def __init__(self, model: str = "claude-sonnet-4-5") -> None:
        self.model = model
        self.llm = FakeLLM(model=model)

    @observe(name="agent.run", as_type="agent", capture_input=False, capture_output=False)
    def run(
        self,
        user_id: str,
        feature: str,
        session_id: str,
        intent: str,
        message: str,
        telemetry_override: TelemetryOverride | None = None,
        correlation_id: str | None = None,
        langfuse_trace_id: str | None = None,
        record_failure_metrics: bool = True,
    ) -> AgentResult:
        bind_contextvars(feature=feature, intent=intent, model=self.model)

        started = time.perf_counter()
        query_preview = summarize_text(message)
        incident_flags = [name for name, enabled in incident_status().items() if enabled]
        langfuse = get_langfuse_client()
        with trace_attributes(
            trace_name=f"chat.{intent}",
            user_id=hash_user_id(user_id),
            session_id=session_id,
            tags=[
                "lab",
                "ecommerce_cskh",
                f"intent:{intent}",
                f"feature:{feature}",
                f"model:{self.model}",
            ]
            + [f"incident:{name}" for name in incident_flags],
            metadata={
                "correlation_id": correlation_id or "missing",
                "feature": feature,
                "intent": intent,
                "model": self.model,
                "app_env": os.getenv("APP_ENV", "dev"),
                "incident_flags": ",".join(incident_flags) if incident_flags else "none",
                "trace_seed": correlation_id or "none",
            },
        ):
            langfuse.update_current_span(
                input={
                    "message_preview": query_preview,
                    "feature": feature,
                    "intent": intent,
                    "correlation_id": correlation_id or "missing",
                    "langfuse_trace_id": langfuse_trace_id,
                },
                metadata={
                    "telemetry_override": bool(telemetry_override),
                    "request_kind": "customer_support_chat",
                },
            )

            try:
                docs, _ = self._run_retrieve(message, telemetry_override=telemetry_override)
                prompt = f"Feature={feature}\nIntent={intent}\nDocs={docs}\nQuestion={message}"
                response, _ = self._run_generate(prompt, query_preview, telemetry_override=telemetry_override)
                quality_score = (
                    telemetry_override.quality_score
                    if telemetry_override and telemetry_override.quality_score is not None
                    else self._heuristic_quality(message, response.text, docs)
                )
                latency_ms = self._finalize_latency(started, telemetry_override.latency_ms if telemetry_override else None)
                cost_usd = (
                    round(telemetry_override.cost_usd, 6)
                    if telemetry_override and telemetry_override.cost_usd is not None
                    else self._estimate_cost(response.usage.input_tokens, response.usage.output_tokens)
                )

                trace_id, trace_url = current_trace_info()
                langfuse.update_current_span(
                    output={
                        "answer_preview": summarize_text(response.text),
                        "doc_count": len(docs),
                        "quality_score": quality_score,
                    },
                    metadata={
                        "trace_id": trace_id,
                        "trace_url": trace_url,
                        "doc_count": len(docs),
                    },
                )

                metrics.record_request(
                    latency_ms=latency_ms,
                    cost_usd=cost_usd,
                    tokens_in=response.usage.input_tokens,
                    tokens_out=response.usage.output_tokens,
                    quality_score=quality_score,
                    intent=intent,
                    feature=feature,
                    success=True,
                )

                return AgentResult(
                    answer=response.text,
                    latency_ms=latency_ms,
                    tokens_in=response.usage.input_tokens,
                    tokens_out=response.usage.output_tokens,
                    cost_usd=cost_usd,
                    quality_score=quality_score,
                    trace_id=trace_id,
                    trace_url=trace_url,
                )
            except Exception as exc:
                if record_failure_metrics:
                    latency_ms = int((time.perf_counter() - started) * 1000)
                    metrics.record_request(
                        latency_ms=latency_ms,
                        cost_usd=0.0,
                        tokens_in=0,
                        tokens_out=0,
                        quality_score=0.0,
                        intent=intent,
                        feature=feature,
                        success=False,
                    )
                langfuse.update_current_span(
                    output={"error_type": type(exc).__name__},
                    metadata={"status": "failed"},
                    level="ERROR",
                    status_message=str(exc),
                )
                raise

    @observe_step("rag.retrieve", as_type="retriever")
    def _run_retrieve(
        self, message: str, telemetry_override: TelemetryOverride | None = None
    ) -> tuple[list[str], int]:
        query_preview = summarize_text(message)
        langfuse = get_langfuse_client()
        log.info(
            "tool_call_started",
            service="agent",
            tool_name="rag.retrieve",
            payload={"query_preview": query_preview},
        )
        started = time.perf_counter()
        try:
            langfuse.update_current_span(
                input={"query_preview": query_preview},
                metadata={"tool_name": "rag.retrieve"},
            )
            docs = retrieve(message)
            latency_ms = self._finalize_latency(
                started,
                telemetry_override.rag_latency_ms if telemetry_override else None,
            )
            metrics.record_tool_latency("rag.retrieve", latency_ms)
            langfuse.update_current_span(
                output={
                    "doc_count": len(docs),
                    "doc_preview": summarize_text(" ".join(docs), max_len=120),
                },
                metadata={"query_preview": query_preview},
            )
            log.info(
                "tool_call_succeeded",
                service="agent",
                tool_name="rag.retrieve",
                latency_ms=latency_ms,
                payload={"doc_count": len(docs), "query_preview": query_preview},
            )
            return docs, latency_ms
        except Exception as exc:
            latency_ms = int((time.perf_counter() - started) * 1000)
            metrics.record_tool_latency("rag.retrieve", latency_ms)
            langfuse.update_current_span(
                metadata={"query_preview": query_preview},
                level="ERROR",
                status_message=str(exc),
            )
            log.error(
                "tool_call_failed",
                service="agent",
                tool_name="rag.retrieve",
                latency_ms=latency_ms,
                error_type=type(exc).__name__,
                payload={"detail": str(exc), "query_preview": query_preview},
            )
            raise

    @observe_step("llm.generate", as_type="generation")
    def _run_generate(
        self,
        prompt: str,
        query_preview: str,
        telemetry_override: TelemetryOverride | None = None,
    ) -> tuple[FakeResponse, int]:
        langfuse = get_langfuse_client()
        log.info(
            "tool_call_started",
            service="agent",
            tool_name="llm.generate",
            payload={"prompt_chars": len(prompt), "query_preview": query_preview},
        )
        started = time.perf_counter()
        try:
            langfuse.update_current_generation(
                model=self.model,
                input={"query_preview": query_preview, "prompt_chars": len(prompt)},
                metadata={"tool_name": "llm.generate"},
            )
            response = self.llm.generate(prompt)
            response = self._apply_usage_override(response, telemetry_override)
            latency_ms = self._finalize_latency(
                started,
                telemetry_override.llm_latency_ms if telemetry_override else None,
            )
            metrics.record_tool_latency("llm.generate", latency_ms)
            langfuse.update_current_generation(
                output={"answer_preview": summarize_text(response.text)},
                model=response.model,
                usage_details=self._usage_details(response),
                cost_details=self._cost_details(response, telemetry_override),
                metadata={"prompt_chars": len(prompt), "query_preview": query_preview},
            )
            log.info(
                "tool_call_succeeded",
                service="agent",
                tool_name="llm.generate",
                latency_ms=latency_ms,
                tokens_in=response.usage.input_tokens,
                tokens_out=response.usage.output_tokens,
                payload={"prompt_chars": len(prompt), "query_preview": query_preview},
            )
            return response, latency_ms
        except Exception as exc:
            latency_ms = int((time.perf_counter() - started) * 1000)
            metrics.record_tool_latency("llm.generate", latency_ms)
            langfuse.update_current_generation(
                metadata={"prompt_chars": len(prompt), "query_preview": query_preview},
                level="ERROR",
                status_message=str(exc),
            )
            log.error(
                "tool_call_failed",
                service="agent",
                tool_name="llm.generate",
                latency_ms=latency_ms,
                error_type=type(exc).__name__,
                payload={"detail": str(exc), "query_preview": query_preview},
            )
            raise

    def _estimate_cost(self, tokens_in: int, tokens_out: int) -> float:
        input_cost = (tokens_in / 1_000_000) * 3
        output_cost = (tokens_out / 1_000_000) * 15
        return round(input_cost + output_cost, 6)

    def _cost_details(
        self, response: FakeResponse, telemetry_override: TelemetryOverride | None
    ) -> dict[str, float]:
        if telemetry_override and telemetry_override.cost_usd is not None:
            return {"total": round(telemetry_override.cost_usd, 6)}

        input_cost = round((response.usage.input_tokens / 1_000_000) * 3, 6)
        output_cost = round((response.usage.output_tokens / 1_000_000) * 15, 6)
        return {"input": input_cost, "output": output_cost, "total": round(input_cost + output_cost, 6)}

    def _usage_details(self, response: FakeResponse) -> dict[str, int]:
        total_tokens = response.usage.input_tokens + response.usage.output_tokens
        return {
            "input": response.usage.input_tokens,
            "output": response.usage.output_tokens,
            "total": total_tokens,
        }

    def _finalize_latency(self, started: float, target_latency_ms: int | None) -> int:
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        if target_latency_ms is None or target_latency_ms <= elapsed_ms:
            return elapsed_ms

        time.sleep((target_latency_ms - elapsed_ms) / 1000)
        return target_latency_ms

    def _apply_usage_override(
        self, response: FakeResponse, telemetry_override: TelemetryOverride | None
    ) -> FakeResponse:
        if telemetry_override is None:
            return response

        tokens_in = telemetry_override.tokens_in
        tokens_out = telemetry_override.tokens_out
        if tokens_in is None and tokens_out is None:
            return response

        return FakeResponse(
            text=response.text,
            usage=type(response.usage)(
                input_tokens=tokens_in if tokens_in is not None else response.usage.input_tokens,
                output_tokens=tokens_out if tokens_out is not None else response.usage.output_tokens,
            ),
            model=response.model,
        )

    def _heuristic_quality(self, question: str, answer: str, docs: list[str]) -> float:
        score = 0.5
        if docs:
            score += 0.2
        if len(answer) > 40:
            score += 0.1
        if question.lower().split()[0:1] and any(token in answer.lower() for token in question.lower().split()[:3]):
            score += 0.1
        if "[REDACTED" in answer:
            score -= 0.2
        return round(max(0.0, min(1.0, score)), 2)
