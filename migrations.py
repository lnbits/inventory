from lnbits.db import Database


async def m001_initial(db: Database):
    """
    -- Table: inventories
    -- Purpose: Stores user-created inventories, each representing a collection of items
       (e.g., a store or warehouse). Supports global discount and tax settings for all
       items in the inventory.
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


async def m002_add_omit_tags(db: Database):
    """
    Add omit_tags column to inventories for existing databases.
    """
    existing_column = await db.fetchone(
        """
        SELECT 1
        FROM pragma_table_info('inventories')
        WHERE name = 'omit_tags'
        """
    )
    if not existing_column:
        await db.execute(
            """
            ALTER TABLE inventory.inventories
            ADD COLUMN omit_tags TEXT;
            """
        )

    """
    -- Table: categories
    -- Purpose: Stores categories for organizing items within an inventory
       (e.g., "Clothing", "Electronics").
       Facilitates filtering in POS, webshop, or reports.
    """
    await db.execute(
        f"""
        CREATE TABLE IF NOT EXISTS inventory.categories (
            id TEXT PRIMARY KEY,
            inventory_id TEXT NOT NULL,
            name TEXT,
            description TEXT,
            created_at TIMESTAMP NOT NULL DEFAULT {db.timestamp_now},
            updated_at TIMESTAMP NOT NULL DEFAULT {db.timestamp_now}
        );
    """
    )


async def m003_add_item_omit_tags(db: Database):
    """
    Add omit_tags column to items for existing databases.
    """
    # Ensure items table exists with omit_tags column for fresh installs
    await db.execute(
        f"""
        CREATE TABLE IF NOT EXISTS inventory.items (
            id TEXT PRIMARY KEY,
            inventory_id TEXT NOT NULL,
            categories TEXT,
            name TEXT NOT NULL,
            description TEXT,
            images TEXT,
            sku TEXT,
            quantity_in_stock INTEGER CHECK (quantity_in_stock IS NULL OR quantity_in_stock >= 0),
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

    existing_column = await db.fetchone(
        """
        SELECT 1
        FROM pragma_table_info('items')
        WHERE name = 'omit_tags'
        """
    )
    if not existing_column:
        await db.execute(
            """
            ALTER TABLE inventory.items
            ADD COLUMN omit_tags TEXT;
            """
        )

    """
    -- Table: Managers
    -- Purpose: Stores managers assigned to specific inventories for better item and stock management.
    """
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

    """
    -- Table: Audit Logs
    -- Purpose: Records all significant actions taken within the inventory system,
       including item updates and stock changes.
    """
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
