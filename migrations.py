from lnbits.db import Database


async def m001_initial(db: Database):
    """
    Fresh install schema for the inventory extension.
    Creates inventories, items, managers, and audit_logs tables with omit_tags included.
    """
    await db.execute(
        f"""
        CREATE TABLE IF NOT EXISTS inventory.inventories (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            name TEXT NOT NULL,
            currency TEXT NOT NULL,
            global_discount_percentage REAL DEFAULT 0.00,
            default_tax_rate REAL DEFAULT 0.00,
            is_tax_inclusive BOOLEAN DEFAULT TRUE,
            tags TEXT,
            omit_tags TEXT,
            created_at TIMESTAMP NOT NULL DEFAULT {db.timestamp_now},
            updated_at TIMESTAMP NOT NULL DEFAULT {db.timestamp_now}
        );
        """
    )

    await db.execute(
        f"""
        CREATE TABLE IF NOT EXISTS inventory.items (
            id TEXT PRIMARY KEY,
            inventory_id TEXT NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            images TEXT,
            sku TEXT,
            quantity_in_stock INTEGER CHECK (
                quantity_in_stock IS NULL OR quantity_in_stock >= 0
            ),
            price REAL NOT NULL,
            discount_percentage REAL DEFAULT 0.00,
            tax_rate REAL,
            reorder_threshold INTEGER,
            unit_cost REAL,
            external_id TEXT,
            is_active BOOLEAN DEFAULT TRUE,
            tags TEXT,
            omit_tags TEXT,
            internal_note TEXT,
            manager_id TEXT,
            is_approved BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP NOT NULL DEFAULT {db.timestamp_now},
            updated_at TIMESTAMP NOT NULL DEFAULT {db.timestamp_now}
        );
        """
    )

    await db.execute(
        f"""
        CREATE TABLE IF NOT EXISTS inventory.managers (
            id TEXT PRIMARY KEY,
            inventory_id TEXT NOT NULL,
            name TEXT NOT NULL,
            email TEXT,
            tags TEXT,
            created_at TIMESTAMP NOT NULL DEFAULT {db.timestamp_now},
            updated_at TIMESTAMP NOT NULL DEFAULT {db.timestamp_now}
        );
        """
    )

    await db.execute(
        f"""
        CREATE TABLE IF NOT EXISTS inventory.audit_logs (
            id {db.serial_primary_key},
            inventory_id TEXT NOT NULL,
            item_id TEXT NOT NULL,
            quantity_change INTEGER NOT NULL,
            quantity_before INTEGER NOT NULL,
            quantity_after INTEGER NOT NULL,
            source TEXT NOT NULL,
            idempotency_key TEXT NOT NULL,
            metadata TEXT,
            created_at TIMESTAMP NOT NULL DEFAULT {db.timestamp_now}
        );
        """
    )
