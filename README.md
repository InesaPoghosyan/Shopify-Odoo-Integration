# Shopify ↔ Odoo Integration

> A clean, developer-friendly bridge between Shopify and Odoo — built to keep both systems in sync without relying on a heavyweight middleware platform.

## What this is

If you run a store on **Shopify** but manage inventory, accounting, and fulfillment in **Odoo**, the two systems need to agree on the same data. This repository will hold a small, readable integration that keeps them talking to each other automatically.

## What's coming

This repo will grow into a working sync engine with the following pieces:

- **Product sync** — Shopify products and variants mirrored into Odoo as `product.product` records, matched by SKU so re-running the sync never creates duplicates.
- **Customer sync** — Shopify customers mirrored into Odoo `res.partner` records, matched by email.
- **Order sync** — Shopify orders turned into Odoo `sale.order` records, with line items linked to the correct products and customers.
- **A simple CLI** — run the full sync or just one piece of it (`--products`, `--customers`, `--orders`, `--all`).
- **Safe by design** — every sync operation is an upsert (create-or-update), so nothing gets duplicated even if you run it a hundred times.

## How it will work

Shopify (Admin REST API) feeds data into a sync engine, which pushes and updates matching records in Odoo (XML-RPC API). Each entity — products, customers, orders — gets its own independent sync module, so you'll be able to run them separately or all together.

## Status

🚧 **Early stage** — this README describes the plan. Code is being added incrementally, piece by piece, so you can follow the project as it takes shape.

## License

MIT
