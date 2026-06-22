"""Query Cache - LRU caching for query results.

Per v3.6 Phase 38: Performance optimization for frequently accessed data.
"""

from collections import OrderedDict
from typing import Any, Optional
from datetime import datetime, timedelta
import hashlib
import json


class QueryCache:
    """LRU cache with TTL for query results.

    Attributes:
        max_size: Maximum number of cached entries.
        default_ttl: Default time-to-live in seconds.
    """

    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        """Initialize cache.

        Args:
            max_size: Maximum cache entries (default: 1000).
            default_ttl: Default TTL in seconds (default: 300 = 5 min).
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: OrderedDict[str, tuple[Any, datetime]] = OrderedDict()
        self._hits = 0
        self._misses = 0

    def _make_key(self, query: str, params: dict) -> str:
        """Generate cache key from query and parameters.

        Args:
            query: Query string.
            params: Query parameters.

        Returns:
            SHA256 hash key.
        """
        data = json.dumps({"query": query, "params": params}, sort_keys=True)
        return hashlib.sha256(data.encode()).hexdigest()

    def get(self, query: str, params: dict) -> Optional[Any]:
        """Get cached result.

        Args:
            query: Query string.
            params: Query parameters.

        Returns:
            Cached result or None if not found/expired.
        """
        key = self._make_key(query, params)

        if key not in self._cache:
            self._misses += 1
            return None

        result, expires_at = self._cache[key]

        # Check TTL
        if datetime.now() > expires_at:
            del self._cache[key]
            self._misses += 1
            return None

        # Move to end (most recently used)
        self._cache.move_to_end(key)
        self._hits += 1
        return result

    def set(self, query: str, params: dict, result: Any, ttl: Optional[int] = None) -> None:
        """Cache a result.

        Args:
            query: Query string.
            params: Query parameters.
            result: Result to cache.
            ttl: Time-to-live in seconds (optional, uses default if None).
        """
        key = self._make_key(query, params)
        expires_at = datetime.now() + timedelta(seconds=ttl or self.default_ttl)

        # Remove if exists (to update position)
        if key in self._cache:
            del self._cache[key]

        # Add new entry
        self._cache[key] = (result, expires_at)

        # Evict oldest if over capacity
        while len(self._cache) > self.max_size:
            self._cache.popitem(last=False)

    def invalidate(self, query: str, params: dict) -> None:
        """Remove specific entry from cache.

        Args:
            query: Query string.
            params: Query parameters.
        """
        key = self._make_key(query, params)
        if key in self._cache:
            del self._cache[key]

    def clear(self) -> None:
        """Clear all cached entries."""
        self._cache.clear()
        self._hits = 0
        self._misses = 0

    def stats(self) -> dict:
        """Get cache statistics.

        Returns:
            Dict with hits, misses, size, hit_rate.
        """
        total = self._hits + self._misses
        hit_rate = (self._hits / total * 100) if total > 0 else 0.0
        return {
            "hits": self._hits,
            "misses": self._misses,
            "size": len(self._cache),
            "max_size": self.max_size,
            "hit_rate_percent": round(hit_rate, 2),
        }


# Global cache instance
_cache: Optional[QueryCache] = None


def get_cache() -> QueryCache:
    """Get global cache instance (singleton).

    Returns:
        QueryCache instance.
    """
    global _cache
    if _cache is None:
        _cache = QueryCache()
    return _cache
