<a href="https://lnbits.com" target="_blank" rel="noopener noreferrer">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://i.imgur.com/QE6SIrs.png">
    <img src="https://i.imgur.com/fyKPgVT.png" alt="LNbits" style="width:280px">
  </picture>
</a>

[![License: MIT](https://img.shields.io/badge/License-MIT-success?logo=open-source-initiative&logoColor=white)](./LICENSE)
[![Built for LNbits](https://img.shields.io/badge/Built%20for-LNbits-4D4DFF?logo=lightning&logoColor=white)](https://github.com/lnbits/lnbits)

# Inventory Extension – <small>[LNbits](https://github.com/lnbits/lnbits) extension</small>

The **Inventory extension** provides a simple and flexible inventory manager for
tracking items, metadata, and stock quantities.

It is designed to work **standalone** or as a **shared inventory source** for other
LNbits extensions that need to reference products, prices, or availability
(for example PoS-style extensions).

## Overview

Inventory offers a centralized way to manage products inside LNbits while keeping
the data reusable across multiple extensions.

Instead of each extension maintaining its own product list, Inventory can act as
a single source of truth for item data and stock levels.

## Highlights

- Create, edit, and manage inventory items
- Track stock quantities with quick inline updates
- Store item metadata such as names, descriptions, and tags
- Tag items for easier filtering and organization
- Share inventory data across multiple LNbits extensions

## Typical Use Cases

- Managing products for point-of-sale or checkout extensions
- Reusing item data across multiple LNbits extensions
- Tracking availability and stock changes over time
- Keeping product information centralized and consistent

## Standalone and Integrations

The Inventory extension can be used on its own as a lightweight inventory manager.

When used alongside other LNbits extensions, it can provide:

- Shared access to item definitions
- Centralized stock tracking
- Consistent product metadata across different workflows

This makes it especially useful for PoS-style setups and other extensions that
depend on structured product data.

## Screenshots

![Inventory manager overview](static/1.png)
![Inventory item details](static/2.png)
![Inventory manager table](static/3.png)

## Notes

- Inventory focuses on item management and availability, not payments.
- Extensions that integrate with Inventory remain responsible for their own
  payment logic and workflows.

## Powered by LNbits

[LNbits](https://lnbits.com) is a free and open-source lightning accounts system.

[![Visit LNbits Shop](https://img.shields.io/badge/Visit-LNbits%20Shop-7C3AED?logo=shopping-cart&logoColor=white&labelColor=5B21B6)](https://shop.lnbits.com/)
[![Try myLNbits SaaS](https://img.shields.io/badge/Try-myLNbits%20SaaS-2563EB?logo=lightning&logoColor=white&labelColor=1E40AF)](https://my.lnbits.com/login)
