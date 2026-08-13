"""
Minimal wrapper around Odoo's external API (XML-RPC).

Odoo exposes two endpoints we need:
  - /xmlrpc/2/common  -> authentication
  - /xmlrpc/2/object  -> read/search/create/write on any model

This wrapper keeps the raw XML-RPC calls in one place so the sync
modules can just call `.search_read(...)`, `.create(...)`, `.write(...)`.
"""

import xmlrpc.client
from typing import Any

from .config import OdooConfig


class OdooClient:
    def __init__(self, config: OdooConfig):
        self.config = config
        self._common = xmlrpc.client.ServerProxy(f"{config.url}/xmlrpc/2/common")
        self._models = xmlrpc.client.ServerProxy(f"{config.url}/xmlrpc/2/object")
        self._uid = self._common.authenticate(config.db, config.username, config.password, {})

        if not self._uid:
            raise RuntimeError("Odoo authentication failed — check ODOO_DB/USERNAME/PASSWORD.")

    def _execute(self, model: str, method: str, *args: Any) -> Any:
        return self._models.execute_kw(
            self.config.db, self._uid, self.config.password, model, method, list(args)
        )

    def search_read(
        self, model: str, domain: list, fields: list[str] | None = None, limit: int | None = None
    ) -> list[dict[str, Any]]:
        kwargs = {"fields": fields or []}
        if limit:
            kwargs["limit"] = limit
        return self._execute(model, "search_read", domain, kwargs["fields"])

    def find_one(self, model: str, domain: list) -> int | None:
        ids = self._execute(model, "search", domain, 0, 1)
        return ids[0] if ids else None

    def create(self, model: str, values: dict[str, Any]) -> int:
        return self._execute(model, "create", values)

    def write(self, model: str, record_id: int, values: dict[str, Any]) -> bool:
        return self._execute(model, "write", [record_id], values)

    def upsert(self, model: str, match_domain: list, values: dict[str, Any]) -> int:
        """
        Find a record matching `match_domain`; update it if found,
        otherwise create it. Returns the record id either way.

        This is the core of "sync without duplicates" — every sync
        module uses this instead of blindly calling create().
        """
        record_id = self.find_one(model, match_domain)
        if record_id:
            self.write(model, record_id, values)
            return record_id
        return self.create(model, values)
