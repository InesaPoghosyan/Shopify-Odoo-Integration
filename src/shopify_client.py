"""
Minimal wrapper around the Shopify Admin REST API.

Only the endpoints this integration actually needs are implemented —
products, customers, and orders, all read-only (we treat Shopify as the
source of truth and only ever write back to Odoo).
"""

from typing import Any, Iterator

import requests

from .config import ShopifyConfig


class ShopifyClient:
    def __init__(self, config: ShopifyConfig):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update(
            {
                "X-Shopify-Access-Token": config.access_token,
                "Content-Type": "application/json",
            }
        )

    def _get(self, path: str, params: dict | None = None) -> requests.Response:
        url = f"{self.config.base_url}/{path.lstrip('/')}"
        response = self.session.get(url, params=params, timeout=30)
        response.raise_for_status()
        return response

    def _paginate(self, path: str, root_key: str, params: dict | None = None) -> Iterator[dict[str, Any]]:
        """
        Shopify paginates via a `Link` response header (cursor-based),
        not page numbers — this follows `next` links until exhausted.
        """
        next_url = f"{self.config.base_url}/{path.lstrip('/')}"
        next_params = params or {"limit": 250}

        while next_url:
            response = self.session.get(next_url, params=next_params, timeout=30)
            response.raise_for_status()
            payload = response.json()

            yield from payload.get(root_key, [])

            next_params = None  # the next URL already carries the cursor
            next_url = self._next_page_url(response)

    @staticmethod
    def _next_page_url(response: requests.Response) -> str | None:
        link_header = response.headers.get("Link", "")
        for part in link_header.split(","):
            if 'rel="next"' in part:
                return part.split(";")[0].strip().strip("<>")
        return None

    def list_products(self) -> Iterator[dict[str, Any]]:
        yield from self._paginate("products.json", "products")

    def list_customers(self) -> Iterator[dict[str, Any]]:
        yield from self._paginate("customers.json", "customers")

    def list_orders(self, status: str = "any") -> Iterator[dict[str, Any]]:
        yield from self._paginate("orders.json", "orders", params={"status": status, "limit": 250})
