# Shopify ↔ Odoo Integration

**A clean, developer-friendly bridge between Shopify and Odoo — built to keep both systems in sync without relying on a heavyweight middleware platform.**

## What this is

If you run a store on **Shopify** but manage inventory, accounting, and fulfillment in **Odoo**, the two systems need to agree on the same data. This repository will hold a small, readable integration that keeps them talking to each other automatically.

## What's coming

This repo will grow into a working sync engine with the following pieces. **Product sync** mirrors Shopify products and variants into Odoo as `product.product` records, matched by SKU so re-running the sync never creates duplicates. **Customer sync** mirrors Shopify customers into Odoo `res.partner` records, matched by email. **Order sync** turns Shopify orders into Odoo `sale.order` records, with line items linked to the correct products and customers. A simple CLI lets you run the full sync or just one piece of it (`--products`, `--customers`, `--orders`, `--all`). And it's safe by design: every sync operation is an upsert (create-or-update), so nothing gets duplicated even if you run it a hundred times.

## How product sync works: Odoo's flat structure

Odoo normally represents a sellable item across two linked models working together. `product.template` is the "idea" of a product: its name, category, and the attributes shared across variants. `product.product` is the actual sellable variant: one row per SKU, with its own price and stock.

For a catalog built natively in Odoo, that two-layer model is the right one — one template, many variants (size, color, etc.) grouped underneath it. But Shopify's own product API is already flat: every variant arrives with its own SKU, price, and inventory, with no separate "template" concept to carry over.

So rather than reconstructing Odoo's template ↔ variant relationship on the way in, this integration syncs directly against `product.product` — a flat, one-to-one mapping: **one Shopify variant → one Odoo `product.product` record**, matched by SKU (`default_code`). Odoo creates the underlying `product.template` automatically the first time a product is created, so nothing about that layer needs to be managed by hand.

**Why flat instead of layered.** It's one matching key (SKU) instead of juggling template groupings and variant attributes. It leaves fewer failure modes, since there are no orphaned templates left behind when a variant disappears on the Shopify side. And the sync code mirrors Shopify's own data shape, so it stays easy to read against the API responses it's processing.

**The sync logic:**

```python
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
```

The actual create-or-update decision lives in one shared helper, so every sync module (products, customers, orders) gets the same "safe to re-run" guarantee for free:

```python
def upsert(self, model: str, match_domain: list, values: dict) -> int:
    """
    Find a record matching `match_domain`; update it if found,
    otherwise create it. Returns the record id either way.
    """
    record_id = self.find_one(model, match_domain)
    if record_id:
        self.write(model, record_id, values)
        return record_id
    return self.create(model, values)
```

Because the match is always by SKU, running `sync_products()` a hundred times against the same catalog produces the same hundred `product.product` records every time — never more.

## How it will work

Shopify (Admin REST API) feeds data into a sync engine, which pushes and updates matching records in Odoo (XML-RPC API). Each entity — products, customers, orders — gets its own independent sync module, so you'll be able to run them separately or all together.

## Status

🚧 **Early stage, actively growing** — the core product-sync logic above is written; customer sync, order sync, and the CLI are next.

## License

MIT
