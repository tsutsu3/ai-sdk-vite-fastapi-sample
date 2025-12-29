from typing import Literal

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
    OTLPSpanExporter as OTLPGrpcSpanExporter,
)
from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
    OTLPSpanExporter as OTLPHttpSpanExporter,
)
from opentelemetry.instrumentation.aiohttp_client import AioHttpClientInstrumentor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

from app.core.config import AppConfig

_configured = False
_has_openai = False

try:
    from opentelemetry.instrumentation.openai import OpenAIInstrumentor

    _has_openai = True
except ImportError:
    _has_openai = False


def _exporter_kind(app_config: AppConfig) -> Literal["console", "otlp", "azure"]:
    value = (app_config.otel_exporter or "console").lower()
    if value in {"console", "otlp", "azure"}:
        return value  # type: ignore[return-value]
    return "console"


def _build_exporter(app_config: AppConfig):
    match _exporter_kind(app_config):
        case "console":
            return ConsoleSpanExporter()
        case "otlp":
            protocol = (app_config.otel_exporter_otlp_protocol or "grpc").lower()
            endpoint = app_config.otel_exporter_otlp_endpoint or None
            if protocol == "http":
                return OTLPHttpSpanExporter(endpoint=endpoint)
            return OTLPGrpcSpanExporter(endpoint=endpoint)
        case "azure":
            from azure.monitor.opentelemetry.exporter import AzureMonitorTraceExporter

            return AzureMonitorTraceExporter(
                connection_string=app_config.azure_monitor_connection_string
            )


def configure_telemetry(app_config: AppConfig) -> None:
    global _configured
    if _configured or not app_config.otel_enabled:
        return

    provider = TracerProvider(
        resource=Resource.create({SERVICE_NAME: app_config.otel_service_name})
    )
    provider.add_span_processor(BatchSpanProcessor(_build_exporter(app_config)))
    trace.set_tracer_provider(provider)

    HTTPXClientInstrumentor().instrument()
    RequestsInstrumentor().instrument()
    AioHttpClientInstrumentor().instrument()
    if _has_openai:
        OpenAIInstrumentor().instrument()

    _configured = True


def instrument_app(app, app_config: AppConfig) -> None:
    if not app_config.otel_enabled:
        return
    if getattr(app.state, "otel_instrumented", False):
        return
    FastAPIInstrumentor.instrument_app(app)
    app.state.otel_instrumented = True
