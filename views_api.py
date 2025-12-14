from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException, Query
from lnbits.core.models import User
from lnbits.db import Filters, Page
from lnbits.decorators import (
    check_user_exists,
    optional_user_id,
    parse_filters,
)
from lnbits.helpers import generate_filter_params_openapi

from .crud import (
    create_inventory,
    create_item,
    create_manager,
    delete_inventory,
    delete_inventory_items,
    delete_inventory_managers,
    delete_inventory_update_logs,
    delete_item,
    delete_manager,
    get_inventories,
    get_inventory,
    get_inventory_items,
    get_inventory_items_paginated,
    get_inventory_update_logs_paginated,
    get_item,
    get_items_by_ids,
    get_manager,
    get_manager_items,
    get_managers,
    get_public_inventory,
    manager_can_access_item,
    update_inventory,
    update_item,
    update_manager,
)
from .helpers import split_tags
from .models import (
    CreateInventory,
    CreateItem,
    CreateManager,
    ImportItem,
    ImportItemsPayload,
    Inventory,
    InventoryLogFilters,
    Item,
    ItemFilters,
    Manager,
    ManagerQuantityUpdate,
    PublicItem,
)

inventory_ext_api = APIRouter()
items_filters = parse_filters(ItemFilters)
logs_filters = parse_filters(InventoryLogFilters)


def _to_csv(value: list[str] | str | None) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        cleaned = value.strip()
        return cleaned or None
    cleaned_values = [str(item).strip() for item in value if str(item).strip()]
    return ",".join(cleaned_values) if cleaned_values else None


def _from_csv(value: str | None, separator: str = ",") -> list[str]:
    if not value:
        return []
    parts = [part.strip() for part in value.split(separator)]
    return [part for part in parts if part]


def _normalize_images(value: str | list[str] | None) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    separator = "|||" if "|||" in value else ","
    return _from_csv(value, separator=separator)


def _to_images_csv(value: list[str] | str | None) -> str | None:
    if value is None:
        return None
    if isinstance(value, list):
        cleaned = [str(v).strip() for v in value if str(v).strip()]
        return "|||".join(cleaned) if cleaned else None
    cleaned_str = str(value).strip()
    return cleaned_str or None


def _prepare_import_item(item: ImportItem, inventory_id: str) -> CreateItem:
    return CreateItem(
        inventory_id=inventory_id,
        name=item.name,
        description=item.description,
        images=_to_images_csv(item.images),
        sku=item.sku,
        quantity_in_stock=item.quantity_in_stock,
        price=item.price,
        discount_percentage=item.discount_percentage,
        tax_rate=item.tax_rate,
        reorder_threshold=item.reorder_threshold,
        unit_cost=item.unit_cost,
        external_id=item.external_id,
        tags=_to_csv(item.tags),
        omit_tags=_to_csv(item.omit_tags),
        is_active=item.is_active if item.is_active is not None else True,
        internal_note=item.internal_note,
        manager_id=None,
        is_approved=item.is_approved if item.is_approved is not None else True,
    )


def _manager_allowed_tags(manager: Manager) -> list[str] | None:
    if manager.tags is None:
        return None
    return split_tags(manager.tags)


def _manager_allows_tags(manager: Manager, item_tags: list[str]) -> bool:
    allowed_tags = _manager_allowed_tags(manager)
    if allowed_tags is None:
        return True
    if not allowed_tags:
        return False
    if not item_tags:
        return False
    return all(tag in allowed_tags for tag in item_tags)


@inventory_ext_api.get("/api/v1", status_code=HTTPStatus.OK)
async def api_get_inventories(
    user: User = Depends(check_user_exists),
) -> Inventory | None:
    return await get_inventories(user.id)


@inventory_ext_api.post("/api/v1", status_code=HTTPStatus.CREATED)
async def api_create_inventory(
    inventory: CreateInventory,
    user: User = Depends(check_user_exists),
) -> Inventory:
    return await create_inventory(user.id, inventory)


@inventory_ext_api.put("/api/v1/{inventory_id}", status_code=HTTPStatus.OK)
async def api_update_inventory(
    inventory_id: str,
    data: CreateInventory,
    user: User = Depends(check_user_exists),
) -> Inventory:
    inventory = await get_inventory(user.id, inventory_id)
    if not inventory or inventory.user_id != user.id:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail="Cannot update inventory.",
        )
    for field, value in data.dict().items():
        setattr(inventory, field, value)
    return await update_inventory(inventory)


@inventory_ext_api.delete("/api/v1/{inventory_id}", status_code=HTTPStatus.NO_CONTENT)
async def api_delete_inventory(
    inventory_id: str,
    user: User = Depends(check_user_exists),
) -> None:
    inventory = await get_inventory(user.id, inventory_id)
    if not inventory or inventory.user_id != user.id:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail="Cannot delete inventory.",
        )
    # delete all related data (items, managers, logs) in cascade
    await delete_inventory_items(inventory_id)
    await delete_inventory_managers(inventory_id)
    await delete_inventory_update_logs(inventory_id)
    # finally delete the inventory
    await delete_inventory(user.id, inventory_id)


## ITEMS
@inventory_ext_api.get(
    "/api/v1/items/{inventory_id}/paginated",
    openapi_extra=generate_filter_params_openapi(ItemFilters),
    response_model=Page,
)
async def api_get_items(
    inventory_id: str,
    user_id: str | None = Depends(optional_user_id),
    filters: Filters = Depends(items_filters),
) -> Page:
    inventory = (
        await get_inventory(user_id, inventory_id)
        if user_id
        else await get_public_inventory(inventory_id)
    )

    if not inventory:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail="Inventory not found.",
        )
    page = await get_inventory_items_paginated(inventory_id, filters)

    if user_id and inventory.dict().get("user_id", None) == user_id:
        return Page(data=page.data, total=page.total)
    return Page(
        data=[PublicItem(**item.dict()) for item in page.data], total=page.total
    )


@inventory_ext_api.patch(
    "/api/v1/items/{inventory_id}/quantities", status_code=HTTPStatus.OK
)
async def api_update_item_quantities(
    inventory_id: str,
    ids: list[str] = Query(...),
    quantities: list[int] = Query(...),
    user: User = Depends(check_user_exists),
) -> list[Item]:
    inventory = await get_inventory(user.id, inventory_id)
    if not inventory or inventory.user_id != user.id:
        raise HTTPException(HTTPStatus.NOT_FOUND, "Inventory not found.")
    if len(ids) != len(quantities):
        raise HTTPException(
            HTTPStatus.BAD_REQUEST,
            "ids and quantities must have the same length.",
        )

    items = await get_items_by_ids(inventory_id, ids)
    existing_by_id = {item.id: item for item in items}
    updated_items: list[Item] = []

    for item_id, qty in zip(ids, quantities, strict=False):
        current = existing_by_id.get(item_id)
        if not current:
            continue
        if current.quantity_in_stock is None:
            continue
        new_quantity = max(0, current.quantity_in_stock - qty)
        current.quantity_in_stock = new_quantity
        updated_items.append(await update_item(current))

    return updated_items


@inventory_ext_api.get("/api/v1/items/{inventory_id}/export", status_code=HTTPStatus.OK)
async def api_export_items(
    inventory_id: str, user: User = Depends(check_user_exists)
) -> dict:
    inventory = await get_inventory(user.id, inventory_id)
    if not inventory or inventory.user_id != user.id:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail="Inventory not found.",
        )
    items = await get_inventory_items(inventory_id)
    exportable_items = []
    for item in items:
        data = item.dict()
        data.pop("inventory_id", None)
        data["tags"] = _from_csv(data.get("tags"))
        data["omit_tags"] = _from_csv(data.get("omit_tags"))
        data["images"] = _normalize_images(data.get("images"))
        exportable_items.append(data)
    return {"items": exportable_items}


@inventory_ext_api.post(
    "/api/v1/items/{inventory_id}/import", status_code=HTTPStatus.CREATED
)
async def api_import_items(
    inventory_id: str,
    payload: ImportItemsPayload,
    user: User = Depends(check_user_exists),
) -> list[Item]:
    inventory = await get_inventory(user.id, inventory_id)
    if not inventory or inventory.user_id != user.id:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail="Inventory not found.",
        )
    created_items: list[Item] = []
    for raw_item in payload.items:
        item_data = _prepare_import_item(raw_item, inventory_id)
        created_item = await create_item(item_data)
        created_items.append(created_item)
    return created_items


@inventory_ext_api.post("/api/v1/items", status_code=HTTPStatus.CREATED)
async def api_create_item(
    item: CreateItem,
    user: User = Depends(check_user_exists),
) -> Item | None:
    inventory = await get_inventory(user.id, item.inventory_id)
    if not inventory or inventory.user_id != user.id:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail="Cannot create item.",
        )
    if item.inventory_id != inventory.id:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail="Item does not belong to the specified inventory.",
        )
    return await create_item(item)


@inventory_ext_api.put("/api/v1/items/{item_id}", status_code=HTTPStatus.OK)
async def api_update_item(
    item_id: str,
    item: CreateItem,
    user: User = Depends(check_user_exists),
) -> Item | None:
    inventory = await get_inventory(user.id, item.inventory_id)
    if not inventory or inventory.user_id != user.id:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail="Cannot update item.",
        )
    _item = await get_item(item_id)
    if not _item or _item.inventory_id != inventory.id:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail="Item not found.",
        )
    for field, value in item.dict().items():
        setattr(_item, field, value)
    # Owner updates implicitly approve items (e.g., items submitted by managers)
    _item.is_approved = True
    return await update_item(_item)


@inventory_ext_api.delete("/api/v1/items/{item_id}", status_code=HTTPStatus.NO_CONTENT)
async def api_delete_item(
    item_id: str,
    user: User = Depends(check_user_exists),
) -> None:
    item = await get_item(item_id)
    if not item:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail="Item not found.",
        )
    inventory = await get_inventory(user.id, item.inventory_id)
    if not inventory or inventory.user_id != user.id:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail="Cannot delete item.",
        )
    await delete_item(item_id)


## MANAGERS
@inventory_ext_api.get("/api/v1/managers/{inventory_id}", status_code=HTTPStatus.OK)
async def api_get_managers(
    inventory_id: str,
    user: User = Depends(check_user_exists),
) -> list[Manager]:
    inventory = await get_inventory(user.id, inventory_id)
    if not inventory or inventory.user_id != user.id:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail="Cannot access managers.",
        )
    if not inventory:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail="Inventory not found.",
        )

    return await get_managers(inventory_id)


@inventory_ext_api.post(
    "/api/v1/managers/{inventory_id}", status_code=HTTPStatus.CREATED
)
async def api_create_manager(
    manager: CreateManager,
    user: User = Depends(check_user_exists),
) -> Manager | None:
    inventory = await get_inventory(user.id, manager.inventory_id)
    if not inventory or inventory.user_id != user.id:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail="Cannot create manager.",
        )
    return await create_manager(manager)


@inventory_ext_api.put("/api/v1/managers/{manager_id}", status_code=HTTPStatus.OK)
async def api_update_manager(
    manager_id: str,
    data: CreateManager,
    user: User = Depends(check_user_exists),
) -> Manager | None:
    manager = await get_manager(manager_id)
    if not manager:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail="Manager not found.",
        )
    inventory = await get_inventory(user.id, manager.inventory_id)
    if not inventory or inventory.user_id != user.id:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail="Cannot update manager.",
        )
    for field, value in data.dict().items():
        setattr(manager, field, value)
    return await update_manager(manager)


@inventory_ext_api.get("/api/v1/managers/{manager_id}", status_code=HTTPStatus.OK)
async def api_get_manager(
    manager_id: str,
    user: User = Depends(check_user_exists),
) -> Manager | None:
    manager = await get_manager(manager_id)
    if not manager:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail="Manager not found.",
        )
    inventory = await get_inventory(user.id, manager.inventory_id)
    if not inventory or inventory.user_id != user.id:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail="Cannot access manager.",
        )
    return manager


@inventory_ext_api.delete(
    "/api/v1/managers/{manager_id}", status_code=HTTPStatus.NO_CONTENT
)
async def api_delete_manager(
    manager_id: str,
    user: User = Depends(check_user_exists),
) -> None:
    manager = await get_manager(manager_id)
    if not manager:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail="Manager not found.",
        )
    inventory = await get_inventory(user.id, manager.inventory_id)
    if not inventory or inventory.user_id != user.id:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail="Cannot delete manager.",
        )
    await delete_manager(manager_id)


@inventory_ext_api.get("/api/v1/manager/{manager_id}/items", status_code=HTTPStatus.OK)
async def api_manager_get_items(
    manager_id: str,
) -> list[Item]:
    manager = await get_manager(manager_id)
    if not manager:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail="Manager not found.",
        )
    inventory = await get_public_inventory(manager.inventory_id)
    if not inventory:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail="Cannot access items.",
        )
    if manager.inventory_id != inventory.id:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail="Manager does not belong to the specified inventory.",
        )
    return await get_manager_items(inventory.id, manager)


@inventory_ext_api.post(
    "/api/v1/managers/{manager_id}/item", status_code=HTTPStatus.CREATED
)
async def api_manager_create_item(
    item: CreateItem,
    manager_id: str,
) -> Item | None:
    manager = await get_manager(manager_id)
    if not manager:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail="Manager not found.",
        )
    inventory = await get_public_inventory(manager.inventory_id)
    if not inventory:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail="Cannot create item.",
        )
    if manager.inventory_id != inventory.id:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail="Manager does not belong to the specified inventory.",
        )
    if item.inventory_id != inventory.id:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail="Item does not belong to the specified inventory.",
        )
    item_tags = split_tags(item.tags)
    if not _manager_allows_tags(manager, item_tags):
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN,
            detail="Manager cannot add items with the selected tags.",
        )
    item.manager_id = manager.id
    item.is_approved = False
    return await create_item(item)


@inventory_ext_api.put(
    "/api/v1/managers/{manager_id}/item/{item_id}", status_code=HTTPStatus.OK
)
async def api_manager_update_item(
    item_id: str,
    data: Item,
    manager_id: str,
) -> Item | None:
    item = await get_item(item_id)
    if not item or item.id != item_id:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail="Item not found.",
        )
    manager = await get_manager(manager_id)
    if not manager:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail="Manager not found.",
        )
    inventory = await get_public_inventory(manager.inventory_id)
    if not inventory:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail="Cannot update item.",
        )
    if manager.inventory_id != inventory.id:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail="Manager does not belong to the specified inventory.",
        )
    if data.inventory_id != inventory.id:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail="Item does not belong to the specified inventory.",
        )
    if item.manager_id != manager_id:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail="Item is not managed by the specified manager.",
        )
    item_tags = split_tags(data.tags)
    if not _manager_allows_tags(manager, item_tags):
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN,
            detail="Manager cannot update items with the selected tags.",
        )
    for field, value in data.dict().items():
        setattr(item, field, value)
    item.manager_id = manager.id
    item.is_active = False
    return await update_item(item)


@inventory_ext_api.put(
    "/api/v1/manager/{manager_id}/item/{item_id}/quantity",
    status_code=HTTPStatus.OK,
)
async def api_manager_update_item_quantity(
    item_id: str, manager_id: str, data: ManagerQuantityUpdate
) -> Item:
    manager = await get_manager(manager_id)
    if not manager:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail="Manager not found.",
        )
    inventory = await get_public_inventory(manager.inventory_id)
    if not inventory:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail="Cannot update item.",
        )
    if data.inventory_id != inventory.id:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail="Item does not belong to the specified inventory.",
        )
    item = await get_item(item_id)
    if not item or item.inventory_id != inventory.id:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail="Item not found.",
        )
    if not manager_can_access_item(manager, item):
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN,
            detail="Manager is not allowed to update this item.",
        )
    item.quantity_in_stock = data.quantity_in_stock
    return await update_item(item)


@inventory_ext_api.delete(
    "/api/v1/managers/{manager_id}/item/{item_id}", status_code=HTTPStatus.NO_CONTENT
)
async def api_manager_delete_item(
    item_id: str,
    manager_id: str,
) -> None:
    item = await get_item(item_id)
    if not item or item.id != item_id:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail="Item not found.",
        )
    if item.manager_id != manager_id:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail="Item is not managed by the specified manager.",
        )
    manager = await get_manager(manager_id)
    if not manager:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail="Manager not found.",
        )
    inventory = await get_public_inventory(manager.inventory_id)
    if not inventory:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail="Cannot delete item.",
        )
    if manager.inventory_id != inventory.id:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail="Manager does not belong to the specified inventory.",
        )
    if item.inventory_id != inventory.id:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail="Item does not belong to the specified inventory.",
        )
    await delete_item(item_id)


@inventory_ext_api.get(
    "/api/v1/logs/{inventory_id}/paginated",
    openapi_extra=generate_filter_params_openapi(InventoryLogFilters),
    response_model=Page,
)
async def api_get_inventory_logs(
    inventory_id: str,
    user: User = Depends(check_user_exists),
    filters: Filters = Depends(logs_filters),
) -> Page:
    inventory = await get_inventory(user.id, inventory_id)
    if not inventory or inventory.user_id != user.id:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail="Inventory not found.",
        )

    page = await get_inventory_update_logs_paginated(inventory_id, filters)
    return page
