"""Prometheus metrics for bot and API."""

from prometheus_client import REGISTRY, Counter, Gauge, Histogram

# Bot
bot_commands_total = Counter(
    "bot_commands_total",
    "Total bot commands",
    ["command"],
)
tasks_created_total = Counter(
    "tasks_created_total",
    "Tasks created",
    ["city"],
)
bids_total = Counter(
    "bids_total",
    "Total bids",
)
active_users_gauge = Gauge(
    "active_users_gauge",
    "Active users in the last hour",
)

# HTTP API
http_requests_total = Counter(
    "http_requests_total",
    "HTTP requests",
    ["method", "endpoint"],
)
request_duration_seconds = Histogram(
    "request_duration_seconds",
    "Request duration in seconds",
    ["method", "endpoint"],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
)
db_query_duration_seconds = Histogram(
    "db_query_duration_seconds",
    "Database query duration in seconds",
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0),
)


def get_metrics_registry():
    return REGISTRY
