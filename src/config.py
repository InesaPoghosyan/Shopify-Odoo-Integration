"""
Loads all integration settings from environment variables (via a .env file).

Nothing sensitive is hard-coded here — copy `.env.example` to `.env`
and fill in your own credentials before running anything.
"""

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class ShopifyConfig:
    shop_url: str
    access_token: str
    api_version: str

    @property
    def base_url(self) -> str:
        return f"https://{self.shop_url}/admin/api/{self.api_version}"


@dataclass(frozen=True)
class OdooConfig:
    url: str
    db: str
    username: str
    password: str


def _require(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(
            f"Missing required environment variable: {name}. "
            f"Did you copy .env.example to .env and fill it in?"
        )
    return value


def load_shopify_config() -> ShopifyConfig:
    return ShopifyConfig(
        shop_url=_require("SHOPIFY_SHOP_URL"),
        access_token=_require("SHOPIFY_ACCESS_TOKEN"),
        api_version=os.getenv("SHOPIFY_API_VERSION", "2024-10"),
    )


def load_odoo_config() -> OdooConfig:
    return OdooConfig(
        url=_require("ODOO_URL"),
        db=_require("ODOO_DB"),
        username=_require("ODOO_USERNAME"),
        password=_require("ODOO_PASSWORD"),
    )
