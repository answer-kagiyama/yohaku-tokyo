"""Minimal fakes shaped like real Tokyo CKAN responses (observed 2026-09)."""

import json
import urllib.parse
from collections.abc import Callable
from typing import Any


def resource(rid: str, fmt: str = "CSV", datastore: bool = False, **kw: Any) -> dict[str, Any]:
    return {
        "id": rid,
        "name": kw.pop("name", rid),
        "format": fmt,
        "datastore_active": datastore,
        "url": kw.pop("url", f"https://www.opendata.metro.tokyo.lg.jp/x/{rid}.{fmt.lower()}"),
        "last_modified": kw.pop("last_modified", "2026-01-29T15:00:00"),
        **kw,
    }


def package(name: str, title: str, resources: list[dict[str, Any]], **kw: Any) -> dict[str, Any]:
    return {
        "id": kw.pop("id", f"id-{name}"),
        "name": name,
        "title": title,
        "notes": kw.pop("notes", f"【区】{title}"),
        "organization": {"title": kw.pop("org", "大田区")},
        "license_id": kw.pop("license_id", "CC-BY-4.0"),
        "license_title": kw.pop("license_title", "クリエイティブ・コモンズ 表示（CC BY）"),
        "metadata_modified": kw.pop("metadata_modified", "2026-03-30T14:14:01.871332"),
        "tags": kw.pop("tags", []),
        "extras": kw.pop("extras", [{"key": "更新頻度", "value": "随時"}]),
        "resources": resources,
        **kw,
    }


def datastore_result(fields: list[str], records: list[dict[str, Any]], total: int | None = None):
    return {
        "fields": [{"id": "_id", "type": "int"}] + [{"id": f, "type": "text"} for f in fields],
        "records": records,
        "total": total if total is not None else len(records),
    }


def fake_transport(
    search: dict[str, list[dict[str, Any]]],
    datastore: dict[str, dict[str, Any] | Exception],
    files: dict[str, bytes | Exception] | None = None,
) -> Callable[[str], bytes]:
    """Routes package_search / datastore_search / file URLs to canned data."""

    def transport(url: str) -> bytes:
        if files is not None and url in files:
            body = files[url]
            if isinstance(body, Exception):
                raise body
            return body
        return json.dumps(route(url)).encode()

    def route(url: str) -> Any:
        parsed = urllib.parse.urlparse(url)
        q = dict(urllib.parse.parse_qsl(parsed.query))
        if parsed.path.endswith("/package_search"):
            results = search.get(q["q"], [])
            start, rows = int(q["start"]), int(q["rows"])
            return {
                "success": True,
                "result": {"count": len(results), "results": results[start : start + rows]},
            }
        if parsed.path.endswith("/datastore_search"):
            if q["resource_id"] not in datastore:
                raise AssertionError(f"unexpected datastore call: {q['resource_id']}")
            value = datastore[q["resource_id"]]
            if isinstance(value, Exception):
                raise value
            return {"success": True, "result": value}
        raise AssertionError(f"unexpected url {url}")

    return transport
