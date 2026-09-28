import json
import urllib.error

import pytest

from station_pipeline.http import HttpError, JsonClient


def test_caches_responses(tmp_path):
    calls = []

    def transport(url):
        calls.append(url)
        return json.dumps({"ok": url}).encode()

    client = JsonClient(transport, cache_dir=tmp_path, sleep=lambda s: None)
    assert client.get_json("https://x/a") == {"ok": "https://x/a"}
    assert client.get_json("https://x/a") == {"ok": "https://x/a"}
    assert calls == ["https://x/a"]

    refreshed = JsonClient(transport, cache_dir=tmp_path, refresh=True, sleep=lambda s: None)
    refreshed.get_json("https://x/a")
    assert len(calls) == 2


def test_retries_then_succeeds():
    attempts = {"n": 0}
    sleeps = []

    def transport(url):
        attempts["n"] += 1
        if attempts["n"] < 3:
            raise urllib.error.URLError("boom")
        return b'{"ok": true}'

    client = JsonClient(transport, sleep=sleeps.append, delay_seconds=0.1)
    assert client.get_json("https://x") == {"ok": True}
    assert attempts["n"] == 3
    assert sleeps == [0.2, 0.4]  # no sleep before the very first request


def test_gives_up_after_retries():
    def transport(url):
        raise TimeoutError()

    client = JsonClient(transport, retries=2, sleep=lambda s: None)
    with pytest.raises(HttpError):
        client.get_json("https://x")


def test_invalid_json_raises_http_error():
    client = JsonClient(lambda url: b"<html>", sleep=lambda s: None)
    with pytest.raises(HttpError, match="invalid JSON"):
        client.get_json("https://x")


def test_get_bytes_is_cached(tmp_path):
    calls = []

    def transport(url):
        calls.append(url)
        return b"a,b\n1,2\n"

    client = JsonClient(transport, cache_dir=tmp_path, sleep=lambda s: None)
    assert client.get_bytes("https://x/f.csv") == client.get_bytes("https://x/f.csv")
    assert len(calls) == 1


def test_client_errors_are_not_retried():
    attempts = {"n": 0}

    def transport(url):
        attempts["n"] += 1
        raise urllib.error.HTTPError(url, 404, "Not Found", {}, None)

    client = JsonClient(transport, sleep=lambda s: None)
    with pytest.raises(HttpError, match="not retried"):
        client.get_json("https://x")
    assert attempts["n"] == 1


def test_rate_limit_is_retried():
    attempts = {"n": 0}

    def transport(url):
        attempts["n"] += 1
        if attempts["n"] == 1:
            raise urllib.error.HTTPError(url, 429, "Too Many", {}, None)
        return b"{}"

    assert JsonClient(transport, sleep=lambda s: None).get_json("https://x") == {}
    assert attempts["n"] == 2
