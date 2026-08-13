"""
Syncs Shopify customers -> Odoo res.partner records.

Matching: email address. Customers without an email are skipped since
email is the only reliable natural key Shopify guarantees for contacts.
"""

from src.odoo_client import OdooClient
from src.shopify_client import ShopifyClient


def sync_customers(shopify: ShopifyClient, odoo: OdooClient) -> dict[str, int]:
    created = 0
    updated = 0
    skipped = 0

    for customer in shopify.list_customers():
        email = customer.get("email")
        if not email:
            skipped += 1
            continue

        name = " ".join(
            part for part in [customer.get("first_name"), customer.get("last_name")] if part
        ) or email

        values = {
            "name": name,
            "email": email,
            "phone": customer.get("phone") or False,
            "customer_rank": 1,  # marks this partner as a customer in Odoo
        }

        existing_id = odoo.find_one("res.partner", [("email", "=", email)])
        odoo.upsert("res.partner", [("email", "=", email)], values)

        if existing_id:
            updated += 1
        else:
            created += 1

    return {"created": created, "updated": updated, "skipped": skipped}
