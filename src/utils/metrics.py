"""Simple in-memory metrics for monitoring.

Tracks key business and system metrics. In production,
these would feed into Prometheus/Grafana.
"""

from collections import defaultdict
from datetime import datetime, timedelta
import threading


class MetricsCollector:
    """Collects and reports application metrics."""

    def __init__(self):
        self._counters: dict[str, int] = defaultdict(int)
        self._timings: dict[str, list[float]] = defaultdict(list)
        self._lock = threading.Lock()
        self._start_time = datetime.utcnow()

    def increment(self, metric: str, value: int = 1):
        """Increment a counter metric."""
        with self._lock:
            self._counters[metric] += value

    def record_timing(self, metric: str, duration_ms: float):
        """Record a timing measurement."""
        with self._lock:
            self._timings[metric].append(duration_ms)
            # Keep only last 1000 measurements
            if len(self._timings[metric]) > 1000:
                self._timings[metric] = self._timings[metric][-1000:]

    def get_counter(self, metric: str) -> int:
        return self._counters.get(metric, 0)

    def get_avg_timing(self, metric: str) -> float:
        timings = self._timings.get(metric, [])
        if not timings:
            return 0.0
        return sum(timings) / len(timings)

    def get_report(self) -> dict:
        """Generate a metrics report."""
        uptime = datetime.utcnow() - self._start_time

        return {
            "uptime_seconds": int(uptime.total_seconds()),
            "counters": dict(self._counters),
            "timings": {
                metric: {
                    "avg_ms": round(self.get_avg_timing(metric), 2),
                    "count": len(values),
                    "min_ms": round(min(values), 2) if values else 0,
                    "max_ms": round(max(values), 2) if values else 0,
                }
                for metric, values in self._timings.items()
            },
        }


# Global metrics instance
metrics = MetricsCollector()


# --- Convenience functions ---

def track_message(platform: str):
    """Track an incoming message."""
    metrics.increment("messages.total")
    metrics.increment(f"messages.{platform}")


def track_order():
    """Track a new order."""
    metrics.increment("orders.total")


def track_payment(provider: str, success: bool):
    """Track a payment attempt."""
    metrics.increment("payments.total")
    if success:
        metrics.increment(f"payments.{provider}.success")
    else:
        metrics.increment(f"payments.{provider}.failed")


def track_agent_response(agent: str, duration_ms: float):
    """Track agent response time."""
    metrics.record_timing(f"agent.{agent}.response", duration_ms)


def track_nlp_intent(intent: str):
    """Track detected intents."""
    metrics.increment(f"nlp.intent.{intent}")
