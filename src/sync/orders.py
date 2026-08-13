"""
Syncs Shopify orders -> Odoo sale.order records.

Matching: `client_order_ref` holds the Shopify order name (e.g. "#1042"),
so re-running the sync updates the existing sale order instead of
duplicating it.

Assumes `sync_customers` and `sync_products` have already run at least
once, since orders reference both a partner and product records by
the same natural keys (email / SKU) those modules create.
"""

from src.odoo_client import OdooClient
from src.shopify_client import ShopifyClient


def sync_orders(shopify: ShopifyClient, odoo: OdooClient) -> dict[str, int]:
    created = 0
    updated = 0
    skipped = 0

    for order in shopify.list_orders():
        order_name = order.get("name")  # e.g. "#1042"
        customer_email = (order.get("customer") or {}).get("email") or order.get("email")

        if not order_name or not customer_email:
            skipped += 1
            continue

        partner_id = odoo.find_one("res.partner", [("email", "=", customer_email)])
        if not partner_id:
            # Customer hasn't been synced yet — skip for now, it'll be
            # picked up on the next run after sync_customers() has run.
            skipped += 1
            continue

        order_lines = []
        for line_item in order.get("line_items", []):
            sku = line_item.get("sku")
            product_id = odoo.find_one("product.product", [("default_code", "=", sku)]) if sku else None
            if not product_id:
                continue

            order_lines.append(
                (
                    0,
                    0,
                    {
                        "product_id": product_id,
                        "product_uom_qty": line_item.get("quantity", 1),
                        "price_unit": float(line_item.get("price", 0) or 0),
                    },
                )
            )

        values = {
            "partner_id": partner_id,
            "client_order_ref": order_name,
            "order_line": order_lines,
        }

        existing_id = odoo.find_one("sale.order", [("client_order_ref", "=", order_name)])
        odoo.upsert("sale.order", [("client_order_ref", "=", order_name)], values)

        if existing_id:
            updated += 1
        else:
            created += 1

    return {"created": created, "updated": updated, "skipped": skipped}
