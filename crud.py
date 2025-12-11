from datetime import datetime, timezone

from lnbits.db import Database, Filters, Page
from lnbits.helpers import urlsafe_short_hash

from .helpers import check_item_tags, create_api_key, split_tags
from .models import (
    Category,
    CreateCategory,
    CreateExternalService,
    CreateInventory,
    CreateInventoryUpdateLog,
    CreateItem,
    CreateManager,
    ExternalService,
    Inventory,
    InventoryLogFilters,
    InventoryUpdateLog,
    Item,
    ItemFilters,
    Manager,
    PublicInventory,
    PublicItem,
)

db = Database("ext_inventory")


async def get_inventories(user_id: str) -> Inventory | None:
    return await db.fetchone(
        """
        SELECT * FROM inventory.inventories
        WHERE user_id = :user_id
        """,
        {"user_id": user_id},
        model=Inventory,
    )


async def get_inventory(user_id: str, inventory_id: str) -> Inventory | None:
    return await db.fetchone(
        """
            SELECT * FROM inventory.inventories
            WHERE id = :inventory_id AND user_id = :user_id
        """,
        {"inventory_id": inventory_id, "user_id": user_id},
        Inventory,
    )


async def get_public_inventory(inventory_id: str) -> PublicInventory | None:
    return await db.fetchone(
        """
            SELECT * FROM inventory.inventories
            WHERE id = :inventory_id
        """,
        {"inventory_id": inventory_id},
        PublicInventory,
    )


async def create_inventory(user_id: str, data: CreateInventory) -> Inventory:
    inventory_id = urlsafe_short_hash()
    inventory = Inventory(
        id=inventory_id,
        user_id=user_id,
        **data.dict(),
    )
    await db.insert("inventory.inventories", inventory)
    return inventory


async def update_inventory(data: Inventory) -> Inventory:
    data.updated_at = datetime.now(timezone.utc)
    await db.update("inventory.inventories", data)
    return data


async def delete_inventory(user_id: str, inventory_id: str) -> None:
    await db.execute(
        """
        DELETE FROM inventory.inventories
        WHERE id = :inventory_id AND user_id = :user_id
        """,
        {"inventory_id": inventory_id, "user_id": user_id},
    )


async def get_inventory_categories(inventory_id: str) -> list[Category]:
    return await db.fetchall(
        """
        SELECT * FROM inventory.categories
        WHERE inventory_id = :inventory_id
        """,
        {"inventory_id": inventory_id},
        model=Category,
    )


async def create_category(data: CreateCategory) -> Category:
    category_id = urlsafe_short_hash()
    category = Category(
        id=category_id,
        **data.dict(),
    )
    await db.insert("inventory.categories", category)
    return category


async def is_category_unique(name: str, inventory_id: str) -> bool:
    existing_category = await db.fetchone(
        """
        SELECT * FROM inventory.categories
        WHERE name = :name AND inventory_id = :inventory_id
        """,
        {"name": name, "inventory_id": inventory_id},
        model=Category,
    )
    return existing_category is None


async def get_inventory_items_paginated(
    inventory_id: str, filters: Filters[ItemFilters] | None = None
) -> Page[Item]:
    where = ["inventory_id = :inventory_id"]
    params = {"inventory_id": inventory_id}

    print("Fetching items with filters:", filters)

    return await db.fetch_page(
        "SELECT * FROM inventory.items",
        where=where,
        values=params,
        filters=filters,
        model=Item,
    )


async def get_items_by_ids(inventory_id: str, item_ids: list[str]) -> list[Item]:
    if not item_ids:
        return []
    if isinstance(item_ids, str):
        item_ids = [item_ids]
    q = ",".join([f"'{item_id}'" for item_id in item_ids])
    items = await db.fetchall(
        f"""
        SELECT * FROM inventory.items
        WHERE inventory_id = :inventory_id AND id IN ({q})
        """,
        {"inventory_id": inventory_id},
        model=Item,
    )
    return items


async def get_item(item_id: str) -> Item | None:
    return await db.fetchone(
        """
        SELECT * FROM inventory.items
        WHERE id = :item_id
        """,
        {"item_id": item_id},
        model=Item,
    )


async def create_item(data: CreateItem) -> Item:
    item_id = urlsafe_short_hash()
    item = Item(
        id=item_id,
        **data.dict(),
    )
    if item.manager_id is not None and item.manager_id != "":
        item.is_active = False  # Items created by managers are inactive by default
    await db.insert("inventory.items", item)
    return item


async def update_item(data: Item) -> Item:
    data.updated_at = datetime.now(timezone.utc)
    await db.update("inventory.items", data)
    return data


async def delete_item(item_id: str) -> None:
    await db.execute(
        """
        DELETE FROM inventory.items
        WHERE id = :item_id
        """,
        {"item_id": item_id},
    )


async def delete_inventory_items(inventory_id: str) -> None:
    await db.execute(
        """
        DELETE FROM inventory.items
        WHERE inventory_id = :inventory_id
        """,
        {"inventory_id": inventory_id},
    )


async def create_manager(data: CreateManager) -> Manager:
    manager_id = urlsafe_short_hash()
    manager = Manager(
        id=manager_id,
        **data.dict(),
    )
    await db.insert("inventory.managers", manager)
    return manager


async def update_manager(data: Manager) -> Manager:
    data.updated_at = datetime.now(timezone.utc)
    await db.update("inventory.managers", data)
    return data


async def get_managers(inventory_id: str) -> list[Manager]:
    return await db.fetchall(
        """
        SELECT * FROM inventory.managers
        WHERE inventory_id = :inventory_id
        """,
        {"inventory_id": inventory_id},
        model=Manager,
    )


async def get_manager(manager_id: str) -> Manager | None:
    return await db.fetchone(
        """
        SELECT * FROM inventory.managers
        WHERE id = :manager_id
        """,
        {"manager_id": manager_id},
        model=Manager,
    )


async def delete_manager(manager_id: str) -> None:
    await db.execute(
        """
        DELETE FROM inventory.managers
        WHERE id = :manager_id
        """,
        {"manager_id": manager_id},
    )


async def delete_inventory_managers(inventory_id: str) -> None:
    await db.execute(
        """
        DELETE FROM inventory.managers
        WHERE inventory_id = :inventory_id
        """,
        {"inventory_id": inventory_id},
    )


async def get_inventory_items(inventory_id: str) -> list[Item]:
    return await db.fetchall(
        """
        SELECT * FROM inventory.items
        WHERE inventory_id = :inventory_id
        """,
        {"inventory_id": inventory_id},
        model=Item,
    )


def manager_can_access_item(manager: Manager, item: Item) -> bool:
    # No restriction when manager has no tag limitations
    if manager.tags is None:
        return True

    allowed_tags = split_tags(manager.tags)
    # Explicitly disallow when the manager has no allowed tags configured
    if not allowed_tags:
        return False

    item_tags = split_tags(item.tags)
    if not item_tags:
        return False

    return check_item_tags(allowed_tags, item_tags)


async def get_manager_items(inventory_id: str, manager: Manager) -> list[Item]:
    items = await get_inventory_items(inventory_id)
    return [item for item in items if manager_can_access_item(manager, item)]


async def create_external_service(data: CreateExternalService) -> ExternalService:
    service_id = urlsafe_short_hash()
    ext_service = ExternalService(
        id=service_id,
        api_key=create_api_key(data.inventory_id, service_id),
        **data.dict(),
    )
    await db.insert("inventory.external_services", ext_service)
    return ext_service


async def get_external_service(service_id: str) -> ExternalService | None:
    return await db.fetchone(
        """
        SELECT * FROM inventory.external_services
        WHERE id = :service_id
        """,
        {"service_id": service_id},
        model=ExternalService,
    )


async def get_external_service_by_api_key(api_key: str) -> ExternalService | None:
    return await db.fetchone(
        """
        SELECT * FROM inventory.external_services
        WHERE api_key = :api_key
        """,
        {"api_key": api_key},
        model=ExternalService,
    )


async def get_external_services() -> list[ExternalService]:
    return await db.fetchall(
        """
        SELECT * FROM inventory.external_services
        """,
        model=ExternalService,
    )


async def delete_external_service(service_id: str) -> None:
    await db.execute(
        """
        DELETE FROM inventory.external_services
        WHERE id = :service_id
        """,
        {"service_id": service_id},
    )


async def delete_inventory_external_services(inventory_id: str) -> None:
    await db.execute(
        """
        DELETE FROM inventory.external_services
        WHERE inventory_id = :inventory_id
        """,
        {"inventory_id": inventory_id},
    )


async def update_external_service(data: ExternalService) -> ExternalService:
    data.last_used_at = datetime.now(timezone.utc)
    await db.update("inventory.external_services", data)
    return data


## Log/Audit
async def create_inventory_update_log(
    data: CreateInventoryUpdateLog,
) -> None:
    await db.insert("inventory.audit_logs", data)


async def get_inventory_update_logs_paginated(
    inventory_id: str,
    filters: Filters[InventoryLogFilters] | None = None,
) -> Page[InventoryUpdateLog]:
    where = ["inventory_id = :inventory_id"]
    params = {"inventory_id": inventory_id}

    return await db.fetch_page(
        "SELECT * FROM inventory.audit_logs",
        where=where,
        values=params,
        filters=filters,
        model=InventoryUpdateLog,
    )


async def delete_inventory_update_logs(inventory_id: str) -> None:
    await db.execute(
        """
        DELETE FROM inventory.audit_logs
        WHERE inventory_id = :inventory_id
        """,
        {"inventory_id": inventory_id},
    )


async def check_idempotency(idempotency_key: str) -> bool:
    """
    Check if this request has already been processed.
    Returns True if already processed.
    """
    existing_log = await db.fetchone(
        """
        SELECT * FROM inventory.audit_logs
        WHERE idempotency_key = :idempotency_key
        """,
        {"idempotency_key": idempotency_key},
        model=InventoryUpdateLog,
    )
    return existing_log is not None
