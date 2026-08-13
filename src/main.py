"""
Entry point for the Shopify <-> Odoo sync.

Usage:
    python -m src.main --all
    python -m src.main --products
    python -m src.main --customers
    python -m src.main --orders
"""

import argparse

from src.config import load_odoo_config, load_shopify_config
from src.odoo_client import OdooClient
from src.shopify_client import ShopifyClient
from src.sync.customers import sync_customers
from src.sync.orders import sync_orders
from src.sync.products import sync_products


def build_clients() -> tuple[ShopifyClient, OdooClient]:
    shopify = ShopifyClient(load_shopify_config())
    odoo = OdooClient(load_odoo_config())
    return shopify, odoo


def main() -> None:
    parser = argparse.ArgumentParser(description="Sync data between Shopify and Odoo.")
    parser.add_argument("--all", action="store_true", help="Sync products, customers, and orders.")
    parser.add_argument("--products", action="store_true", help="Sync products only.")
    parser.add_argument("--customers", action="store_true", help="Sync customers only.")
    parser.add_argument("--orders", action="store_true", help="Sync orders only.")
    args = parser.parse_args()

    if not any([args.all, args.products, args.customers, args.orders]):
        parser.error("Specify at least one of --all, --products, --customers, --orders.")

    shopify, odoo = build_clients()

    # Order matters: customers and products should exist before orders
    # try to reference them.
    if args.all or args.customers:
        result = sync_customers(shopify, odoo)
        print(f"Customers -> created: {result['created']}, updated: {result['updated']}, skipped: {result['skipped']}")

    if args.all or args.products:
        result = sync_products(shopify, odoo)
        print(f"Products  -> created: {result['created']}, updated: {result['updated']}, skipped: {result['skipped']}")

    if args.all or args.orders:
        result = sync_orders(shopify, odoo)
        print(f"Orders    -> created: {result['created']}, updated: {result['updated']}, skipped: {result['skipped']}")


if __name__ == "__main__":
    main()
