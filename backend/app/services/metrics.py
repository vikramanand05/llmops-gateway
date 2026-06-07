from prometheus_client import Counter, Gauge, Histogram

REQUEST_COUNT = Counter(
    "llmops_gateway_requests_total",
    "HTTP request count",
    ["route", "method", "status"],
)
ERROR_COUNT = Counter(
    "llmops_gateway_errors_total",
    "HTTP error count",
    ["route", "method", "status"],
)
REQUEST_LATENCY = Histogram(
    "llmops_gateway_request_latency_seconds",
    "HTTP request latency",
    ["route", "method"],
)
LLM_COST_TOTAL = Counter(
    "llmops_gateway_cost_total",
    "Estimated LLM cost",
    ["provider", "model"],
)
FALLBACK_COUNT = Counter(
    "llmops_gateway_fallbacks_total",
    "Fallbacks used by the router",
    ["from_model", "to_model"],
)
PROVIDER_HEALTH = Gauge(
    "llmops_gateway_provider_health",
    "Provider health status, 1 healthy and 0 unhealthy",
    ["provider"],
)
