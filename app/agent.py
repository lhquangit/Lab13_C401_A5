from __future__ import annotations

import time
from dataclasses import dataclass

from structlog.contextvars import bind_contextvars

from . import metrics
from .incidents import status as incident_status
from .logging_config import get_logger
from .mock_llm import FakeLLM, FakeResponse
from .mock_rag import retrieve
from .pii import hash_user_id, summarize_text
from .tracing import langfuse_context, observe, observe_step

log = get_logger()


@dataclass
class AgentResult:
    answer: str
    latency_ms: int
    tokens_in: int
    tokens_out: int
    cost_usd: float
    quality_score: float


class LabAgent:
    def __init__(self, model: str = "claude-sonnet-4-5") -> None:
        self.model = model
        self.llm = FakeLLM(model=model)

    @observe(name="agent.run")
    def run(self, user_id: str, feature: str, session_id: str, intent: str, message: str) -> AgentResult:
        bind_contextvars(feature=feature, intent=intent, model=self.model)

        started = time.perf_counter()
        query_preview = summarize_text(message)
        incident_flags = [name for name, enabled in incident_status().items() if enabled]
        langfuse_context.update_current_trace(
            user_id=hash_user_id(user_id),
            session_id=session_id,
            tags=["lab", "ecommerce_cskh", intent, feature, self.model]
            + [f"incident:{name}" for name in incident_flags],
        )
        langfuse_context.update_current_observation(
            metadata={
                "intent": intent,
                "feature": feature,
                "incident_flags": incident_flags,
                "query_preview": query_preview,
            }
        )

        try:
            docs, _ = self._run_retrieve(message)
            prompt = f"Feature={feature}\nIntent={intent}\nDocs={docs}\nQuestion={message}"
            response, _ = self._run_generate(prompt, query_preview)
            quality_score = self._heuristic_quality(message, response.text, docs)
            latency_ms = int((time.perf_counter() - started) * 1000)
            cost_usd = self._estimate_cost(response.usage.input_tokens, response.usage.output_tokens)

            langfuse_context.update_current_observation(
                metadata={
                    "doc_count": len(docs),
                    "intent": intent,
                    "query_preview": query_preview,
                    "incident_flags": incident_flags,
                },
                usage_details={"input": response.usage.input_tokens, "output": response.usage.output_tokens},
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
            )
        except Exception:
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
            raise

    @observe_step("rag.retrieve")
    def _run_retrieve(self, message: str) -> tuple[list[str], int]:
        query_preview = summarize_text(message)
        log.info(
            "tool_call_started",
            service="agent",
            tool_name="rag.retrieve",
            payload={"query_preview": query_preview},
        )
        started = time.perf_counter()
        try:
            docs = retrieve(message)
            latency_ms = int((time.perf_counter() - started) * 1000)
            metrics.record_tool_latency("rag.retrieve", latency_ms)
            langfuse_context.update_current_observation(
                metadata={"doc_count": len(docs), "query_preview": query_preview}
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
            langfuse_context.update_current_observation(metadata={"query_preview": query_preview})
            log.error(
                "tool_call_failed",
                service="agent",
                tool_name="rag.retrieve",
                latency_ms=latency_ms,
                error_type=type(exc).__name__,
                payload={"detail": str(exc), "query_preview": query_preview},
            )
            raise

    @observe_step("llm.generate")
    def _run_generate(self, prompt: str, query_preview: str) -> tuple[FakeResponse, int]:
        log.info(
            "tool_call_started",
            service="agent",
            tool_name="llm.generate",
            payload={"prompt_chars": len(prompt), "query_preview": query_preview},
        )
        started = time.perf_counter()
        try:
            response = self.llm.generate(prompt)
            latency_ms = int((time.perf_counter() - started) * 1000)
            metrics.record_tool_latency("llm.generate", latency_ms)
            langfuse_context.update_current_observation(
                usage_details={"input": response.usage.input_tokens, "output": response.usage.output_tokens},
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
            langfuse_context.update_current_observation(
                metadata={"prompt_chars": len(prompt), "query_preview": query_preview}
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
