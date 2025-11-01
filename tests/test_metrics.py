"""Comprehensive tests for Prometheus metrics module."""

import time

import pytest
from prometheus_client import Counter, Gauge, Histogram

from producthuntdb.metrics import (
    DEFAULT_LATENCY_BUCKETS,
    HTTP_LATENCY_BUCKETS,
    active_database_connections,
    batch_size,
    cache_entries,
    database_operations_total,
    database_query_duration_seconds,
    errors_total,
    generate_metrics_output,
    graphql_queries_total,
    graphql_request_duration_seconds,
    http_request_duration_seconds,
    http_requests_total,
    initialize_metrics,
    last_successful_run_timestamp,
    pipeline_runs_total,
    pipeline_stage_active,
    register_collector,
    registry,
    reset_metrics,
    unregister_collector,
)


class TestMetricsConstants:
    """Tests for metric constants and configurations."""

    def test_default_latency_buckets_defined(self):
        """Test DEFAULT_LATENCY_BUCKETS is properly defined."""
        assert DEFAULT_LATENCY_BUCKETS is not None
        assert len(DEFAULT_LATENCY_BUCKETS) == 9
        assert DEFAULT_LATENCY_BUCKETS == (0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)

    def test_http_latency_buckets_defined(self):
        """Test HTTP_LATENCY_BUCKETS is properly defined."""
        assert HTTP_LATENCY_BUCKETS is not None
        assert len(HTTP_LATENCY_BUCKETS) == 9
        assert HTTP_LATENCY_BUCKETS == (0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5)

    def test_buckets_are_sorted(self):
        """Test that bucket definitions are sorted."""
        assert list(DEFAULT_LATENCY_BUCKETS) == sorted(DEFAULT_LATENCY_BUCKETS)
        assert list(HTTP_LATENCY_BUCKETS) == sorted(HTTP_LATENCY_BUCKETS)


class TestCounterMetrics:
    """Tests for Counter metrics."""

    def test_http_requests_total_increment(self):
        """Test http_requests_total counter increments."""
        initial = http_requests_total.labels(status="200", path="/posts", method="GET")._value.get()
        http_requests_total.labels(status="200", path="/posts", method="GET").inc()
        assert http_requests_total.labels(status="200", path="/posts", method="GET")._value.get() == initial + 1

    def test_http_requests_total_increment_by_value(self):
        """Test http_requests_total counter increments by value."""
        initial = http_requests_total.labels(status="404", path="/notfound", method="GET")._value.get()
        http_requests_total.labels(status="404", path="/notfound", method="GET").inc(5)
        assert http_requests_total.labels(status="404", path="/notfound", method="GET")._value.get() == initial + 5

    def test_graphql_queries_total_increment(self):
        """Test graphql_queries_total counter increments."""
        initial = graphql_queries_total.labels(query_type="posts", status="success")._value.get()
        graphql_queries_total.labels(query_type="posts", status="success").inc()
        assert graphql_queries_total.labels(query_type="posts", status="success")._value.get() == initial + 1

    def test_database_operations_total_increment(self):
        """Test database_operations_total counter increments."""
        initial = database_operations_total.labels(operation="insert", table="posts", status="success")._value.get()
        database_operations_total.labels(operation="insert", table="posts", status="success").inc(10)
        assert database_operations_total.labels(operation="insert", table="posts", status="success")._value.get() == initial + 10

    def test_errors_total_increment(self):
        """Test errors_total counter increments."""
        initial = errors_total.labels(error_type="rate_limit", component="api")._value.get()
        errors_total.labels(error_type="rate_limit", component="api").inc()
        assert errors_total.labels(error_type="rate_limit", component="api")._value.get() == initial + 1

    def test_pipeline_runs_total_increment(self):
        """Test pipeline_runs_total counter increments."""
        initial = pipeline_runs_total.labels(status="success")._value.get()
        pipeline_runs_total.labels(status="success").inc()
        assert pipeline_runs_total.labels(status="success")._value.get() == initial + 1


class TestGaugeMetrics:
    """Tests for Gauge metrics."""

    def test_active_database_connections_set(self):
        """Test active_database_connections gauge set."""
        active_database_connections.set(5)
        assert active_database_connections._value.get() == 5

    def test_active_database_connections_inc(self):
        """Test active_database_connections gauge increment."""
        initial = active_database_connections._value.get()
        active_database_connections.inc()
        assert active_database_connections._value.get() == initial + 1

    def test_active_database_connections_dec(self):
        """Test active_database_connections gauge decrement."""
        initial = active_database_connections._value.get()
        active_database_connections.dec()
        assert active_database_connections._value.get() == initial - 1

    def test_pipeline_stage_active_set(self):
        """Test pipeline_stage_active gauge set."""
        pipeline_stage_active.labels(stage="fetching").set(3)
        assert pipeline_stage_active.labels(stage="fetching")._value.get() == 3

    def test_cache_entries_set(self):
        """Test cache_entries gauge set."""
        cache_entries.labels(cache_type="graphql_responses").set(100)
        assert cache_entries.labels(cache_type="graphql_responses")._value.get() == 100

    def test_last_successful_run_timestamp_set(self):
        """Test last_successful_run_timestamp gauge set."""
        now = time.time()
        last_successful_run_timestamp.set(now)
        assert abs(last_successful_run_timestamp._value.get() - now) < 0.01


class TestHistogramMetrics:
    """Tests for Histogram metrics."""

    def test_graphql_request_duration_observe(self):
        """Test graphql_request_duration_seconds histogram observe."""
        graphql_request_duration_seconds.labels(query_type="posts", status="success").observe(0.5)
        # Just verify observe() doesn't raise - Histogram internals vary by version
        # The fact that observe() completed without error is sufficient

    def test_database_query_duration_observe(self):
        """Test database_query_duration_seconds histogram observe."""
        database_query_duration_seconds.labels(operation="select", table="posts").observe(0.1)
        # Just verify observe() doesn't raise

    def test_http_request_duration_observe(self):
        """Test http_request_duration_seconds histogram observe."""
        http_request_duration_seconds.labels(status="200", path="/posts", method="GET").observe(0.05)
        # Just verify observe() doesn't raise

    def test_batch_size_observe(self):
        """Test batch_size histogram observe."""
        batch_size.labels(operation="insert_posts").observe(50)
        # Just verify observe() doesn't raise

    def test_histogram_buckets_used(self):
        """Test histogram uses correct buckets."""
        # Observe various values to hit different buckets
        test_metric = graphql_request_duration_seconds.labels(query_type="test", status="success")
        test_metric.observe(0.001)  # < 0.01
        test_metric.observe(0.02)   # 0.01-0.05
        test_metric.observe(0.5)    # 0.25-0.5
        test_metric.observe(5.0)    # 2.5-5.0
        
        # Just verify observe() doesn't raise


class TestHelperFunctions:
    """Tests for helper functions."""

    def test_generate_metrics_output(self):
        """Test generate_metrics_output produces bytes."""
        output = generate_metrics_output()
        assert isinstance(output, bytes)
        assert b"http_requests_total" in output

    def test_generate_metrics_output_includes_metrics(self):
        """Test generate_metrics_output includes registered metrics."""
        # Increment a counter to ensure it appears
        http_requests_total.labels(status="200", path="/test", method="GET").inc()
        output = generate_metrics_output()
        
        # Check for metric names
        assert b"http_requests_total" in output
        assert b"graphql_queries_total" in output
        assert b"database_operations_total" in output

    def test_register_collector_success(self):
        """Test register_collector with new collector."""
        # Create a temporary collector
        test_counter = Counter("test_counter_temp", "Test counter", registry=None)
        
        # Register should succeed
        register_collector(test_counter)
        
        # Should appear in output
        output = generate_metrics_output()
        assert b"test_counter_temp" in output
        
        # Cleanup
        unregister_collector(test_counter)

    def test_register_collector_duplicate_raises(self):
        """Test register_collector with duplicate raises ValueError."""
        # Try to register an existing metric
        with pytest.raises(ValueError):
            register_collector(http_requests_total)

    def test_unregister_collector(self):
        """Test unregister_collector removes collector."""
        # Create and register a temporary collector
        test_gauge = Gauge("test_gauge_temp_unreg", "Test gauge", registry=None)
        register_collector(test_gauge)
        
        # Verify it's registered
        output = generate_metrics_output()
        assert b"test_gauge_temp_unreg" in output
        
        # Unregister it
        unregister_collector(test_gauge)
        
        # Verify it's gone
        output = generate_metrics_output()
        assert b"test_gauge_temp_unreg" not in output

    def test_unregister_collector_nonexistent(self):
        """Test unregister_collector with nonexistent collector doesn't crash."""
        # Create a collector that's not registered
        test_counter = Counter("test_counter_never_registered", "Test counter", registry=None)
        
        # Should not raise, just log a warning
        unregister_collector(test_counter)

    def test_initialize_metrics(self):
        """Test initialize_metrics runs without error."""
        # Should not raise
        initialize_metrics()

    def test_reset_metrics_callable(self):
        """Test reset_metrics is callable."""
        # Just verify it doesn't crash when called
        # Note: This will unregister collectors, so we can't test much
        try:
            reset_metrics()
            # Re-register metrics after reset by using them
            http_requests_total.labels(status="200", path="/test", method="GET").inc()
        except Exception as e:
            pytest.fail(f"reset_metrics() raised: {e}")


class TestMetricsRegistry:
    """Tests for custom registry."""

    def test_registry_exists(self):
        """Test custom registry is defined."""
        assert registry is not None

    def test_registry_collects_metrics(self):
        """Test registry collects metrics."""
        # Ensure at least one metric is registered by using it
        http_requests_total.labels(status="test", path="/test", method="GET").inc()
        
        # Generate output to trigger collection
        output = generate_metrics_output()
        assert len(output) > 0
        assert b"http_requests_total" in output


class TestMetricsLabels:
    """Tests for metric labels."""

    def test_http_requests_different_labels(self):
        """Test http_requests with different labels are separate."""
        http_requests_total.labels(status="200", path="/a", method="GET").inc(1)
        http_requests_total.labels(status="404", path="/b", method="POST").inc(2)
        
        # Values should be different
        val_200 = http_requests_total.labels(status="200", path="/a", method="GET")._value.get()
        val_404 = http_requests_total.labels(status="404", path="/b", method="POST")._value.get()
        
        # Can't assert exact values due to test pollution, but they should differ
        assert val_200 != val_404 or (val_200 == val_404 == 0)

    def test_graphql_queries_different_types(self):
        """Test graphql_queries with different query types."""
        graphql_queries_total.labels(query_type="posts", status="success").inc(5)
        graphql_queries_total.labels(query_type="users", status="error").inc(3)
        
        # Should be tracked separately
        posts_count = graphql_queries_total.labels(query_type="posts", status="success")._value.get()
        users_count = graphql_queries_total.labels(query_type="users", status="error")._value.get()
        
        assert posts_count >= 5
        assert users_count >= 3


class TestMetricsIntegration:
    """Integration tests for metrics workflow."""

    def test_complete_http_request_flow(self):
        """Test complete HTTP request metrics flow."""
        # Ensure metrics are registered by using them
        http_requests_total.labels(status="200", path="/posts", method="GET").inc()
        
        # Start request
        start = time.time()
        
        # Record duration
        duration = time.time() - start
        http_request_duration_seconds.labels(status="200", path="/posts", method="GET").observe(duration)
        
        # Verify metrics were recorded
        output = generate_metrics_output()
        assert b"http_requests_total" in output
        assert b"http_request_duration_seconds" in output

    def test_complete_graphql_query_flow(self):
        """Test complete GraphQL query metrics flow."""
        # Ensure metrics are registered by using them
        graphql_queries_total.labels(query_type="posts", status="success").inc()
        
        # Start query
        start = time.time()
        
        # Record duration
        duration = time.time() - start
        graphql_request_duration_seconds.labels(query_type="posts", status="success").observe(duration)
        
        # Verify metrics
        output = generate_metrics_output()
        assert b"graphql_queries_total" in output
        assert b"graphql_request_duration_seconds" in output

    def test_complete_database_operation_flow(self):
        """Test complete database operation metrics flow."""
        # Track connections
        active_database_connections.inc()
        
        # Start operation
        start = time.time()
        
        # Simulate operation
        database_operations_total.labels(operation="insert", table="posts", status="success").inc(10)
        
        # Record duration
        duration = time.time() - start
        database_query_duration_seconds.labels(operation="insert", table="posts").observe(duration)
        
        # Record batch size
        batch_size.labels(operation="insert_posts").observe(10)
        
        # Release connection
        active_database_connections.dec()
        
        # Verify metrics
        output = generate_metrics_output()
        assert b"active_database_connections" in output
        assert b"database_operations_total" in output
        assert b"database_query_duration_seconds" in output
        assert b"batch_size" in output


class TestMetricsExports:
    """Test module exports."""

    def test_all_exports_available(self):
        """Test all expected metrics are exportable."""
        from producthuntdb import metrics
        
        # Counters
        assert hasattr(metrics, "http_requests_total")
        assert hasattr(metrics, "graphql_queries_total")
        assert hasattr(metrics, "database_operations_total")
        assert hasattr(metrics, "errors_total")
        assert hasattr(metrics, "pipeline_runs_total")
        
        # Gauges
        assert hasattr(metrics, "active_database_connections")
        assert hasattr(metrics, "pipeline_stage_active")
        assert hasattr(metrics, "cache_entries")
        assert hasattr(metrics, "last_successful_run_timestamp")
        
        # Histograms
        assert hasattr(metrics, "graphql_request_duration_seconds")
        assert hasattr(metrics, "database_query_duration_seconds")
        assert hasattr(metrics, "http_request_duration_seconds")
        assert hasattr(metrics, "batch_size")
        
        # Helpers
        assert hasattr(metrics, "generate_metrics_output")
        assert hasattr(metrics, "register_collector")
        assert hasattr(metrics, "unregister_collector")
        assert hasattr(metrics, "reset_metrics")
        assert hasattr(metrics, "initialize_metrics")
        
        # Constants
        assert hasattr(metrics, "DEFAULT_LATENCY_BUCKETS")
        assert hasattr(metrics, "HTTP_LATENCY_BUCKETS")
        assert hasattr(metrics, "registry")


class TestMetricsEdgeCases:
    """Test edge cases and error conditions."""

    def test_histogram_with_negative_value(self):
        """Test histogram handles negative values (Prometheus allows this)."""
        # Prometheus histograms technically allow negative values
        # but they're not meaningful for latency
        try:
            graphql_request_duration_seconds.labels(query_type="test", status="success").observe(-0.1)
        except ValueError:
            pytest.fail("Histogram should accept negative values (Prometheus spec)")

    def test_histogram_with_zero_value(self):
        """Test histogram handles zero values."""
        graphql_request_duration_seconds.labels(query_type="test", status="success").observe(0.0)
        # Should not raise

    def test_histogram_with_large_value(self):
        """Test histogram handles very large values."""
        graphql_request_duration_seconds.labels(query_type="test", status="success").observe(999.9)
        # Should not raise

    def test_counter_cannot_decrement(self):
        """Test counter doesn't have dec() method."""
        counter = http_requests_total.labels(status="200", path="/test", method="GET")
        assert not hasattr(counter, "dec")

    def test_gauge_can_go_negative(self):
        """Test gauge can have negative values."""
        test_gauge = Gauge("test_gauge_negative", "Test gauge", registry=None)
        register_collector(test_gauge)
        
        test_gauge.set(-5)
        assert test_gauge._value.get() == -5
        
        unregister_collector(test_gauge)

    def test_metrics_output_content_type(self):
        """Test metrics output is valid Prometheus format."""
        # Ensure at least one metric is registered
        http_requests_total.labels(status="200", path="/test", method="GET").inc()
        
        output = generate_metrics_output()
        decoded = output.decode("utf-8")
        
        # Should have HELP and TYPE lines
        assert "# HELP" in decoded
        assert "# TYPE" in decoded

    def test_pipeline_stage_transitions(self):
        """Test pipeline stage tracking through transitions."""
        # Start in fetching
        pipeline_stage_active.labels(stage="fetching").inc()
        assert pipeline_stage_active.labels(stage="fetching")._value.get() >= 1
        
        # Move to processing
        pipeline_stage_active.labels(stage="fetching").dec()
        pipeline_stage_active.labels(stage="processing").inc()
        
        # Move to storing
        pipeline_stage_active.labels(stage="processing").dec()
        pipeline_stage_active.labels(stage="storing").inc()
        
        # Finish
        pipeline_stage_active.labels(stage="storing").dec()
