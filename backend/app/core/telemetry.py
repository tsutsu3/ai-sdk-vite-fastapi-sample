from time import perf_counter
from typing import Literal

from opentelemetry import metrics, trace
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
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import (
    ConsoleMetricExporter,
    PeriodicExportingMetricReader,
)
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

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


def _build_metric_exporter(app_config: AppConfig):
    match _exporter_kind(app_config):
        case "console":
            return ConsoleMetricExporter()
        case "otlp":
            from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import (
                OTLPMetricExporter as OTLPGrpcMetricExporter,
            )
            from opentelemetry.exporter.otlp.proto.http.metric_exporter import (
                OTLPMetricExporter as OTLPHttpMetricExporter,
            )

            protocol = (app_config.otel_exporter_otlp_protocol or "grpc").lower()
            endpoint = app_config.otel_exporter_otlp_endpoint or None
            if protocol == "http":
                return OTLPHttpMetricExporter(endpoint=endpoint)
            return OTLPGrpcMetricExporter(endpoint=endpoint)
        case "azure":
            from azure.monitor.opentelemetry.exporter import AzureMonitorMetricExporter

            return AzureMonitorMetricExporter(
                connection_string=app_config.azure_monitor_connection_string
            )


class RequestMetricsMiddleware(BaseHTTPMiddleware):
    """Emit per-request metrics for latency and error rate."""

    def __init__(self, app, meter_provider: MeterProvider) -> None:
        super().__init__(app)
        meter = meter_provider.get_meter("app.http")
        self._duration = meter.create_histogram(
            "http.server.duration",
            description="HTTP server request duration",
            unit="ms",
        )
        self._requests = meter.create_counter(
            "http.server.request_count",
            description="HTTP server request count",
            unit="1",
        )

    async def dispatch(
        self,
        request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        start = perf_counter()
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        finally:
            elapsed_ms = (perf_counter() - start) * 1000
            route = getattr(request.scope.get("route"), "path", request.url.path)
            attributes = {
                "http.method": request.method,
                "http.route": route,
                "http.status_code": status_code,
            }
            self._duration.record(elapsed_ms, attributes)
            self._requests.add(1, attributes)


def configure_telemetry(app_config: AppConfig) -> None:
    global _configured
    if _configured or not app_config.otel_enabled:
        return

    provider = TracerProvider(
        resource=Resource.create({SERVICE_NAME: app_config.otel_service_name})
    )
    provider.add_span_processor(BatchSpanProcessor(_build_exporter(app_config)))
    trace.set_tracer_provider(provider)

    metric_reader = PeriodicExportingMetricReader(_build_metric_exporter(app_config))
    meter_provider = MeterProvider(
        resource=Resource.create({SERVICE_NAME: app_config.otel_service_name}),
        metric_readers=[metric_reader],
    )
    metrics.set_meter_provider(meter_provider)

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
    meter_provider = metrics.get_meter_provider()
    if isinstance(meter_provider, MeterProvider):
        app.add_middleware(RequestMetricsMiddleware, meter_provider=meter_provider)
    app.state.otel_instrumented = True
