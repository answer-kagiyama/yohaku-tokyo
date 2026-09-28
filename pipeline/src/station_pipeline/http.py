"""Polite, cached HTTP client (stdlib only). Tests inject a fake transport."""

import hashlib
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

USER_AGENT = "yohaku-tokyo-pipeline/0.1 (open data research; local MVP)"

# (url) -> response body. Raises on failure.
Transport = Callable[[str], bytes]


class HttpError(RuntimeError):
    pass


def urllib_transport(url: str, timeout: float = 30.0) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 - https only
        return resp.read()


def build_url(base: str, params: Mapping[str, Any]) -> str:
    return f"{base}?{urllib.parse.urlencode(sorted(params.items()))}"


class HttpClient:
    def __init__(
        self,
        transport: Transport = urllib_transport,
        cache_dir: Path | None = None,
        refresh: bool = False,
        delay_seconds: float = 0.3,
        retries: int = 3,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._transport = transport
        self._cache_dir = cache_dir
        self._refresh = refresh
        self._delay = delay_seconds
        self._retries = retries
        self._sleep = sleep
        self.network_calls = 0

    def _cache_path(self, url: str) -> Path | None:
        if self._cache_dir is None:
            return None
        return self._cache_dir / f"{hashlib.sha1(url.encode()).hexdigest()}.cache"

    def get_bytes(self, url: str) -> bytes:
        cache = self._cache_path(url)
        if cache is not None and cache.exists() and not self._refresh:
            return cache.read_bytes()

        last_error: Exception | None = None
        for attempt in range(self._retries):
            if self.network_calls > 0 or attempt > 0:
                self._sleep(self._delay * (2**attempt))
            self.network_calls += 1
            try:
                body = self._transport(url)
                break
            except urllib.error.HTTPError as exc:
                last_error = exc
                if 400 <= exc.code < 500 and exc.code != 429:
                    raise HttpError(f"GET {url}: HTTP {exc.code} (not retried)") from exc
            except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
                last_error = exc
        else:
            raise HttpError(f"GET failed after {self._retries} attempts: {url}: {last_error}")

        if cache is not None:
            cache.parent.mkdir(parents=True, exist_ok=True)
            cache.write_bytes(body)
        return body

    def get_json(self, url: str) -> Any:
        body = self.get_bytes(url)
        try:
            return json.loads(body)
        except ValueError as exc:
            raise HttpError(f"invalid JSON from {url}: {exc}") from exc


# Backwards-compatible name used by discovery.
JsonClient = HttpClient
