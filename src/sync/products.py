"""
Syncs Shopify products -> Odoo product.product records.

Matching: a Shopify variant's SKU is stored in Odoo's `default_code`.
If a product with that SKU already exists, it's updated in place;
otherwise a new product is created. This makes the sync safe to re-run.
"""

from src.odoo_client import OdooClient
from src.shopify_client import ShopifyClient


def sync_products(shopify: ShopifyClient, odoo: OdooClient) -> dict[str, int]:
    created = 0
    updated = 0
    skipped = 0

    for product in shopify.list_products():
        for variant in product.get("variants", []):
            sku = variant.get("sku")
            if not sku:
                # Can't reliably match a variant without a SKU — skip it
                # rather than risk creating duplicate products.
                skipped += 1
                continue

            values = {
                "name": product["title"],
                "default_code": sku,
                "list_price": float(variant.get("price", 0) or 0),
                "type": "product",  # storable product
            }

            existing_id = odoo.find_one("product.product", [("default_code", "=", sku)])
            odoo.upsert("product.product", [("default_code", "=", sku)], values)

            if existing_id:
                updated += 1
            else:
                created += 1

    return {"created": created, "updated": updated, "skipped": skipped}
