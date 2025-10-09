"""
Prometheus metrics for FinOpsGuard
"""

from prometheus_client import Counter, Histogram, generate_latest, CollectorRegistry, REGISTRY


# Create a custom registry
registry = CollectorRegistry()

# Default metrics
from prometheus_client import start_http_server, CollectorRegistry

# FinOpsGuard specific metrics
checks_total = Counter(
    'finops_checks_total',
    'Total number of cost checks',
    ['result', 'cloud'],
    registry=registry
)

checks_duration = Histogram(
    'finops_checks_duration_seconds',
    'Duration of cost checks',
    buckets=[0.05, 0.1, 0.25, 0.5, 1, 2, 5, 10, 30, 60],
    registry=registry
)

blocks_total = Counter(
    'finops_blocks_total',
    'Total number of blocking policy decisions',
    registry=registry
)

recommendations_total = Counter(
    'finops_recommendations_total',
    'Total number of recommendations emitted',
    registry=registry
)

# Cache metrics
cache_hits = Counter(
    'finops_cache_hits_total',
    'Total number of cache hits',
    ['cache_type'],  # pricing, analysis, terraform
    registry=registry
)

cache_misses = Counter(
    'finops_cache_misses_total',
    'Total number of cache misses',
    ['cache_type'],
    registry=registry
)

cache_errors = Counter(
    'finops_cache_errors_total',
    'Total number of cache errors',
    ['cache_type', 'operation'],  # get, set, delete
    registry=registry
)


def get_metrics_text() -> str:
    """Get Prometheus metrics in text format"""
    return generate_latest(registry).decode('utf-8')
