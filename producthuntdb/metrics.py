"""Prometheus metrics collection and export.

This module provides Prometheus instrumentation for the ProductHunt DB pipeline,
enabling metrics collection for monitoring requests, queries, performance, and system health.

Key Features:
    - Counter metrics for incrementing values (requests, errors, operations)
    - Gauge metrics for fluctuating values (connections, queue sizes)
    - Histogram metrics for distributions (latency buckets, response times)
    - Custom CollectorRegistry for explicit metric control
    - generate_latest() for /metrics endpoint integration
    - Custom bucket definitions optimized for GraphQL/database operations

Metric Types:
    Counters (always increase):
        - http_requests_total: Total HTTP requests by status, path, method
        - graphql_queries_total: Total GraphQL queries by type, status
        - database_operations_total: Total DB operations by type, status
        - errors_total: Total errors by type, component
    
    Gauges (can go up or down):
        - active_database_connections: Current number of DB connections
        - pipeline_stage_active: Number of pipelines in each stage
        - cache_entries: Number of entries in various caches
    
    Histograms (track distributions):
        - graphql_request_duration_seconds: GraphQL query latency
        - database_query_duration_seconds: Database operation latency
        - http_request_duration_seconds: HTTP request latency

Usage:
    Basic counter:
    
    ```python
    from producthuntdb.metrics import http_requests_total
    
    @app.route("/posts")
    def get_posts():
        http_requests_total.labels(
            status="200",
            path="/posts",
            method="GET"
        ).inc()
        return posts
    ```
    
    Gauge for active connections:
    
    ```python
    from producthuntdb.metrics import active_database_connections
    
    def connect_to_db():
        active_database_connections.inc()
        try:
            conn = create_connection()
            return conn
        finally:
            active_database_connections.dec()
    ```
    
    Histogram for tracking latency:
    
    ```python
    from producthuntdb.metrics import graphql_request_duration_seconds
    import time
    
    def execute_query(query):
        start = time.time()
        try:
            result = client.execute(query)
            return result
        finally:
            duration = time.time() - start
            graphql_request_duration_seconds.labels(
                query_type="posts",
                status="success"
            ).observe(duration)
    ```
    
    Exposing metrics endpoint:
    
    ```python
    from flask import Flask
    from producthuntdb.metrics import generate_metrics_output
    
    app = Flask(__name__)
    
    @app.route("/metrics")
    def metrics():
        return generate_metrics_output(), 200, {"Content-Type": "text/plain"}
    ```

Environment Variables:
    - PROMETHEUS_ENABLED: Enable Prometheus metrics (default: true)
    - PROMETHEUS_PORT: Port for metrics endpoint (default: 9090)

References:
    - Prometheus Python Client: https://github.com/prometheus/client_python
    - BetterStack Guide: https://betterstack.com/community/guides/monitoring/prometheus-python-metrics/
    - Metric Types: https://prometheus.io/docs/tutorials/understanding_metric_types/
    - Best Practices: https://prometheus.io/docs/practices/instrumentation/
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from prometheus_client import (
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)

if TYPE_CHECKING:
    from prometheus_client.registry import Collector

from producthuntdb.logging import logger

# Custom registry for explicit metric control
# This avoids default process/platform metrics unless explicitly added
registry = CollectorRegistry()

# Latency bucket definitions (in seconds)
# Optimized for typical GraphQL/database operations
# Covers milliseconds (0.01s) to seconds (10s+)
DEFAULT_LATENCY_BUCKETS = (
    0.01,   # 10ms
    0.05,   # 50ms
    0.1,    # 100ms
    0.25,   # 250ms
    0.5,    # 500ms
    1.0,    # 1s
    2.5,    # 2.5s
    5.0,    # 5s
    10.0,   # 10s
)

# HTTP request buckets (slightly faster expectations)
HTTP_LATENCY_BUCKETS = (
    0.005,  # 5ms
    0.01,   # 10ms
    0.025,  # 25ms
    0.05,   # 50ms
    0.1,    # 100ms
    0.25,   # 250ms
    0.5,    # 500ms
    1.0,    # 1s
    2.5,    # 2.5s
)


# ========== COUNTER METRICS (always increase) ==========

http_requests_total = Counter(
    "http_requests_total",
    "Total number of HTTP requests",
    labelnames=["status", "path", "method"],
    registry=registry,
)
"""Counter for tracking total HTTP requests by status, path, and method.

Labels:
    status: HTTP status code (e.g., "200", "404", "500")
    path: Request path (e.g., "/posts", "/metrics")
    method: HTTP method (e.g., "GET", "POST")

Example:
    ```python
    http_requests_total.labels(status="200", path="/posts", method="GET").inc()
    ```
"""

graphql_queries_total = Counter(
    "graphql_queries_total",
    "Total number of GraphQL queries executed",
    labelnames=["query_type", "status"],
    registry=registry,
)
"""Counter for tracking GraphQL queries by type and status.

Labels:
    query_type: Type of query (e.g., "posts", "users", "topics", "viewer")
    status: Query result status (e.g., "success", "error", "timeout")

Example:
    ```python
    graphql_queries_total.labels(query_type="posts", status="success").inc()
    ```
"""

database_operations_total = Counter(
    "database_operations_total",
    "Total number of database operations",
    labelnames=["operation", "table", "status"],
    registry=registry,
)
"""Counter for tracking database operations by type, table, and status.

Labels:
    operation: Operation type (e.g., "insert", "update", "select", "delete")
    table: Table name (e.g., "posts", "users", "topics")
    status: Operation status (e.g., "success", "error")

Example:
    ```python
    database_operations_total.labels(
        operation="insert",
        table="posts",
        status="success"
    ).inc(50)  # Batch of 50 posts inserted
    ```
"""

errors_total = Counter(
    "errors_total",
    "Total number of errors encountered",
    labelnames=["error_type", "component"],
    registry=registry,
)
"""Counter for tracking errors by type and component.

Labels:
    error_type: Error type (e.g., "rate_limit", "timeout", "validation", "network")
    component: Component where error occurred (e.g., "api", "database", "kaggle")

Example:
    ```python
    errors_total.labels(error_type="rate_limit", component="api").inc()
    ```
"""

pipeline_runs_total = Counter(
    "pipeline_runs_total",
    "Total number of pipeline runs",
    labelnames=["status"],
    registry=registry,
)
"""Counter for tracking complete pipeline runs.

Labels:
    status: Run status (e.g., "success", "partial", "failed")

Example:
    ```python
    pipeline_runs_total.labels(status="success").inc()
    ```
"""


# ========== GAUGE METRICS (can go up or down) ==========

active_database_connections = Gauge(
    "active_database_connections",
    "Current number of active database connections",
    registry=registry,
)
"""Gauge for tracking current active database connections.

Example:
    ```python
    # On connection open
    active_database_connections.inc()
    
    # On connection close
    active_database_connections.dec()
    
    # Set absolute value
    active_database_connections.set(5)
    ```
"""

pipeline_stage_active = Gauge(
    "pipeline_stage_active",
    "Number of pipelines currently in each stage",
    labelnames=["stage"],
    registry=registry,
)
"""Gauge for tracking active pipelines by stage.

Labels:
    stage: Pipeline stage (e.g., "fetching", "processing", "storing", "exporting")

Example:
    ```python
    # Start processing
    pipeline_stage_active.labels(stage="fetching").inc()
    
    # Finish processing
    pipeline_stage_active.labels(stage="fetching").dec()
    ```
"""

cache_entries = Gauge(
    "cache_entries",
    "Number of entries in cache",
    labelnames=["cache_type"],
    registry=registry,
)
"""Gauge for tracking cache entry counts by type.

Labels:
    cache_type: Cache type (e.g., "graphql_responses", "user_lookups")

Example:
    ```python
    cache_entries.labels(cache_type="graphql_responses").set(1250)
    ```
"""

last_successful_run_timestamp = Gauge(
    "last_successful_run_timestamp",
    "Unix timestamp of the last successful pipeline run",
    registry=registry,
)
"""Gauge for tracking when the last successful pipeline run completed.

Example:
    ```python
    import time
    
    last_successful_run_timestamp.set(time.time())
    ```
"""


# ========== HISTOGRAM METRICS (track distributions) ==========

graphql_request_duration_seconds = Histogram(
    "graphql_request_duration_seconds",
    "Duration of GraphQL requests in seconds",
    labelnames=["query_type", "status"],
    buckets=DEFAULT_LATENCY_BUCKETS,
    registry=registry,
)
"""Histogram for tracking GraphQL request latency.

Labels:
    query_type: Type of query (e.g., "posts", "users", "topics")
    status: Query status (e.g., "success", "error")

Buckets: 10ms, 50ms, 100ms, 250ms, 500ms, 1s, 2.5s, 5s, 10s

Example:
    ```python
    import time
    
    start = time.time()
    try:
        result = client.fetch_posts()
        status = "success"
    except Exception:
        status = "error"
    finally:
        duration = time.time() - start
        graphql_request_duration_seconds.labels(
            query_type="posts",
            status=status
        ).observe(duration)
    ```
"""

database_query_duration_seconds = Histogram(
    "database_query_duration_seconds",
    "Duration of database queries in seconds",
    labelnames=["operation", "table"],
    buckets=DEFAULT_LATENCY_BUCKETS,
    registry=registry,
)
"""Histogram for tracking database query latency.

Labels:
    operation: Operation type (e.g., "insert", "select", "update")
    table: Table name (e.g., "posts", "users")

Buckets: 10ms, 50ms, 100ms, 250ms, 500ms, 1s, 2.5s, 5s, 10s

Example:
    ```python
    import time
    
    start = time.time()
    db.execute("INSERT INTO posts ...")
    duration = time.time() - start
    
    database_query_duration_seconds.labels(
        operation="insert",
        table="posts"
    ).observe(duration)
    ```
"""

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "Duration of HTTP requests in seconds",
    labelnames=["status", "path", "method"],
    buckets=HTTP_LATENCY_BUCKETS,
    registry=registry,
)
"""Histogram for tracking HTTP request latency.

Labels:
    status: HTTP status code (e.g., "200", "404")
    path: Request path (e.g., "/posts", "/metrics")
    method: HTTP method (e.g., "GET", "POST")

Buckets: 5ms, 10ms, 25ms, 50ms, 100ms, 250ms, 500ms, 1s, 2.5s

Example:
    ```python
    import time
    
    start = time.time()
    response = app.handle_request()
    duration = time.time() - start
    
    http_request_duration_seconds.labels(
        status="200",
        path="/posts",
        method="GET"
    ).observe(duration)
    ```
"""

batch_size = Histogram(
    "batch_size",
    "Size of batches processed",
    labelnames=["operation"],
    buckets=(1, 5, 10, 25, 50, 100, 250, 500, 1000),
    registry=registry,
)
"""Histogram for tracking batch operation sizes.

Labels:
    operation: Operation type (e.g., "insert_posts", "update_users")

Buckets: 1, 5, 10, 25, 50, 100, 250, 500, 1000

Example:
    ```python
    batch_size.labels(operation="insert_posts").observe(len(posts))
    ```
"""


# ========== HELPER FUNCTIONS ==========

def generate_metrics_output() -> bytes:
    """Generate Prometheus metrics output in text format.
    
    This function generates the /metrics endpoint response containing
    all registered metrics in Prometheus exposition format.
    
    Returns:
        Metrics output as bytes (suitable for HTTP response)
    
    Example:
        ```python
        from flask import Flask
        from producthuntdb.metrics import generate_metrics_output
        
        app = Flask(__name__)
        
        @app.route("/metrics")
        def metrics_endpoint():
            return generate_metrics_output(), 200, {"Content-Type": "text/plain; charset=utf-8"}
        ```
    
    Note:
        This uses the custom registry, so only explicitly registered metrics are included.
    """
    return generate_latest(registry)


def register_collector(collector: Collector) -> None:
    """Register a custom collector with the metrics registry.
    
    Use this to add custom metrics or collectors to the global registry.
    
    Args:
        collector: Prometheus collector to register
    
    Example:
        ```python
        from prometheus_client import Gauge
        from producthuntdb.metrics import register_collector
        
        custom_metric = Gauge("custom_metric", "My custom metric")
        register_collector(custom_metric)
        ```
    
    Raises:
        ValueError: If collector is already registered
    """
    try:
        registry.register(collector)
        logger.debug(f"Registered custom collector: {collector}")
    except ValueError as e:
        logger.warning(f"Collector already registered: {e}")
        raise


def unregister_collector(collector: Collector) -> None:
    """Unregister a collector from the metrics registry.
    
    Args:
        collector: Prometheus collector to unregister
    
    Example:
        ```python
        from producthuntdb.metrics import custom_metric, unregister_collector
        
        unregister_collector(custom_metric)
        ```
    """
    try:
        registry.unregister(collector)
        logger.debug(f"Unregistered collector: {collector}")
    except Exception as e:
        logger.warning(f"Failed to unregister collector: {e}")


def reset_metrics() -> None:
    """Reset all metrics to their initial state.
    
    This is primarily useful for testing. Use with caution in production.
    
    Warning:
        This will reset ALL metrics in the custom registry.
    
    Example:
        ```python
        from producthuntdb.metrics import reset_metrics
        
        # In test teardown
        def teardown():
            reset_metrics()
        ```
    """
    logger.warning("Resetting all Prometheus metrics")
    
    # Clear all collectors and re-register them
    # Note: This is a simplified approach; in production you may want
    # to recreate the registry entirely
    for collector in list(registry._collector_to_names.keys()):
        try:
            registry.unregister(collector)
        except Exception as e:
            logger.error(f"Failed to unregister collector during reset: {e}")


# Initialize metrics system
def initialize_metrics() -> None:
    """Initialize the Prometheus metrics system.
    
    This function logs the initialization and can be extended to add
    default collectors or perform other setup tasks.
    
    Example:
        ```python
        from producthuntdb.metrics import initialize_metrics
        
        # Call once at application startup
        initialize_metrics()
        ```
    """
    logger.info(
        "Prometheus metrics initialized",
        metrics_enabled=True,
        registry_type="custom",
    )


# Export public API
__all__ = [
    # Registry
    "registry",
    # Counters
    "http_requests_total",
    "graphql_queries_total",
    "database_operations_total",
    "errors_total",
    "pipeline_runs_total",
    # Gauges
    "active_database_connections",
    "pipeline_stage_active",
    "cache_entries",
    "last_successful_run_timestamp",
    # Histograms
    "graphql_request_duration_seconds",
    "database_query_duration_seconds",
    "http_request_duration_seconds",
    "batch_size",
    # Helpers
    "generate_metrics_output",
    "register_collector",
    "unregister_collector",
    "reset_metrics",
    "initialize_metrics",
    # Bucket definitions
    "DEFAULT_LATENCY_BUCKETS",
    "HTTP_LATENCY_BUCKETS",
]
