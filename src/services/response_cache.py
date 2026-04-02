"""In-memory LRU response cache.

Replaces Redis dependency for caching. Handles:
1. Caching Claude API responses for common questions
2. Caching NLP intent detection results
3. Caching product search results

Goal: Handle 80%+ of messages without hitting Claude API.
"""

import hashlib
import time
from collections import OrderedDict
from threading import Lock


class LRUCache:
    """Thread-safe in-memory LRU cache with TTL expiry."""

    def __init__(self, max_size: int = 10000, default_ttl: int = 3600):
        self._cache: OrderedDict[str, tuple[any, float]] = OrderedDict()
        self._max_size = max_size
        self._default_ttl = default_ttl
        self._lock = Lock()
        self._hits = 0
        self._misses = 0

    def get(self, key: str) -> any:
        with self._lock:
            if key in self._cache:
                value, expiry = self._cache[key]
                if time.time() < expiry:
                    self._cache.move_to_end(key)
                    self._hits += 1
                    return value
                else:
                    del self._cache[key]
            self._misses += 1
            return None

    def set(self, key: str, value: any, ttl: int | None = None) -> None:
        with self._lock:
            if key in self._cache:
                del self._cache[key]
            elif len(self._cache) >= self._max_size:
                self._cache.popitem(last=False)

            expiry = time.time() + (ttl or self._default_ttl)
            self._cache[key] = (value, expiry)

    def delete(self, key: str) -> bool:
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    def clear(self) -> None:
        with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0

    @property
    def size(self) -> int:
        return len(self._cache)

    @property
    def hit_rate(self) -> float:
        total = self._hits + self._misses
        return self._hits / total if total > 0 else 0.0

    def stats(self) -> dict:
        return {
            "size": self.size,
            "max_size": self._max_size,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": f"{self.hit_rate:.1%}",
        }


def _cache_key(prefix: str, text: str) -> str:
    """Generate a cache key from prefix + text hash."""
    h = hashlib.md5(text.encode()).hexdigest()[:12]
    return f"{prefix}:{h}"


# Global caches
intent_cache = LRUCache(max_size=5000, default_ttl=86400)      # Intent detection: 24h
response_cache = LRUCache(max_size=2000, default_ttl=1800)     # Bot responses: 30min
search_cache = LRUCache(max_size=1000, default_ttl=600)        # Product search: 10min


def cached_intent(text: str) -> tuple[str, float] | None:
    """Get cached intent detection result."""
    key = _cache_key("intent", text.strip().lower())
    return intent_cache.get(key)


def cache_intent(text: str, intent: str, confidence: float) -> None:
    """Cache an intent detection result."""
    key = _cache_key("intent", text.strip().lower())
    intent_cache.set(key, (intent, confidence))


def cached_response(merchant_id: int, text: str) -> str | None:
    """Get cached bot response for a message."""
    key = _cache_key(f"resp:{merchant_id}", text.strip().lower())
    return response_cache.get(key)


def cache_response(merchant_id: int, text: str, response: str) -> None:
    """Cache a bot response."""
    key = _cache_key(f"resp:{merchant_id}", text.strip().lower())
    response_cache.set(key, response)


def cached_search(merchant_id: int, query: str) -> list | None:
    """Get cached product search results."""
    key = _cache_key(f"search:{merchant_id}", query.strip().lower())
    return search_cache.get(key)


def cache_search(merchant_id: int, query: str, results: list) -> None:
    """Cache product search results."""
    key = _cache_key(f"search:{merchant_id}", query.strip().lower())
    search_cache.set(key, results)


def get_all_cache_stats() -> dict:
    """Get stats for all caches."""
    return {
        "intent_cache": intent_cache.stats(),
        "response_cache": response_cache.stats(),
        "search_cache": search_cache.stats(),
    }
