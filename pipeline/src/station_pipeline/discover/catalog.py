"""CKAN catalog access (Tokyo Open Data Catalog)."""

from collections.abc import Iterator
from typing import Any

from ..http import JsonClient, build_url

DEFAULT_CATALOG = "https://catalog.data.metro.tokyo.lg.jp"
PAGE_SIZE = 100


class CkanCatalog:
    def __init__(self, client: JsonClient, base_url: str = DEFAULT_CATALOG) -> None:
        self.client = client
        self.base_url = base_url.rstrip("/")

    def _action(self, name: str, **params: Any) -> Any:
        body = self.client.get_json(build_url(f"{self.base_url}/api/3/action/{name}", params))
        if not body.get("success"):
            raise RuntimeError(f"CKAN {name} failed: {body.get('error')}")
        return body["result"]

    def search(self, keyword: str) -> Iterator[dict[str, Any]]:
        """All packages matching a keyword, following pagination."""
        start = 0
        while True:
            result = self._action("package_search", q=keyword, rows=PAGE_SIZE, start=start)
            yield from result["results"]
            start += PAGE_SIZE
            if start >= result["count"] or not result["results"]:
                return

    def datastore_sample(self, resource_id: str, limit: int = 50) -> dict[str, Any]:
        return self._action("datastore_search", resource_id=resource_id, limit=limit)

    def dataset_page(self, package_name: str) -> str:
        return f"{self.base_url}/dataset/{package_name}"
