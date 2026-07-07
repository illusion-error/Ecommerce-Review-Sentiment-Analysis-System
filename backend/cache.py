"""Redis prediction cache with in-memory fallback."""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from .settings import settings


def normalize_cache_text(text: str) -> str:
    return " ".join((text or "").strip().lower().split())


def prediction_cache_key(text: str) -> str:
    digest = hashlib.sha256(normalize_cache_text(text).encode("utf-8")).hexdigest()
    return f"sentiment:prediction:{digest}"


@dataclass
class PredictionCache:
    """Cache abstraction used by API handlers."""

    _memory: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    _hits: int = 0
    _misses: int = 0
    _redis_client: Any = None
    _redis_checked: bool = False

    def _client(self) -> Any:
        if self._redis_checked:
            return self._redis_client
        self._redis_checked = True
        try:
            import redis

            client = redis.Redis(
                host=settings.redis_host,
                port=settings.redis_port,
                db=settings.redis_db,
                decode_responses=True,
                socket_connect_timeout=0.3,
                socket_timeout=0.3,
            )
            client.ping()
            self._redis_client = client
        except Exception:
            self._redis_client = None
        return self._redis_client

    def get(self, text: str) -> Optional[Dict[str, Any]]:
        key = prediction_cache_key(text)
        client = self._client()
        if client is not None:
            raw = client.get(key)
            if raw:
                self._hits += 1
                return json.loads(raw)
        item = self._memory.get(key)
        if item and item["expires_at"] >= time.time():
            self._hits += 1
            return dict(item["value"])
        self._misses += 1
        return None

    def set(self, text: str, value: Dict[str, Any]) -> None:
        key = prediction_cache_key(text)
        client = self._client()
        if client is not None:
            client.setex(key, settings.cache_ttl_seconds, json.dumps(value, ensure_ascii=False))
            return
        self._memory[key] = {
            "value": dict(value),
            "expires_at": time.time() + settings.cache_ttl_seconds,
        }

    def stats(self) -> Dict[str, Any]:
        total = self._hits + self._misses
        return {
            "backend": "redis" if self._client() is not None else "memory",
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": round(self._hits / total, 4) if total else 0.0,
        }


prediction_cache = PredictionCache()

