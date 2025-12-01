from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from lnbits.core.models import User, WalletTypeInfo
from lnbits.db import Filters, Page
from lnbits.decorators import (
    check_user_exists,
    optional_user_id,
    parse_filters,
    require_admin_key,
    require_invoice_key,
)
from lnbits.helpers import generate_filter_params_openapi

from .crud import (
    check_idempotency,
    create_category,
    create_external_service,
    create_inventory,
    create_inventory_update_log,
    create_item,
    create_manager,
    delete_external_service,
    delete_inventory,
    delete_inventory_external_services,
    delete_inventory_items,
    delete_inventory_managers,
    delete_inventory_update_logs,
    delete_item,
    delete_manager,
    get_external_service,
    get_external_services,
    get_inventories,
    get_inventory,
    get_inventory_categories,
    get_inventory_items_paginated,
    get_inventory_update_logs_paginated,
    get_item,
    get_items_by_ids,
    get_manager,
    get_manager_items,
    get_managers,
    get_public_inventory,
    is_category_unique,
    update_external_service,
    update_inventory,
    update_item,
)
from .helpers import check_item_tags, extract_token_payload
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
    Item,
    ItemFilters,
    Manager,
    PublicItem,
    UpdateSource,
    WebhookPayload,
)

inventory_ext_api = APIRouter()
items_filters = parse_filters(ItemFilters)


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


@inventory_ext_api.delete(
    "/api/v1/{inventory_id}", status_code=HTTPStatus.NO_CONTENT
)
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
    # delete all related data (items, categories, managers, services, logs) in cascade
    await delete_inventory_items(inventory_id)
    await delete_inventory_managers(inventory_id)
    await delete_inventory_external_services(inventory_id)
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


## CATEGORIES
@inventory_ext_api.get("/api/v1/categories/{inventory_id}", status_code=HTTPStatus.OK)
async def api_get_categories(
    inventory_id: str,
) -> list[Category]:
    inventory = await get_public_inventory(inventory_id)
    if not inventory:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail="Inventory not found.",
        )

    return await get_inventory_categories(inventory_id)


@inventory_ext_api.post("/api/v1/categories", status_code=HTTPStatus.CREATED)
async def api_create_category(
    category: CreateCategory,
    user: User = Depends(check_user_exists),
) -> Category:
    inventory = await get_inventory(user.id, category.inventory_id)
    if not inventory or inventory.user_id != user.id:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail="Cannot create category.",
        )
    if not await is_category_unique(category.name, category.inventory_id):
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail="Category name must be unique.",
        )

    return await create_category(category)


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
    return await get_manager_items(inventory.id, manager_id)


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
    data.is_active = False
    return await update_item(data)


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


## external services
@inventory_ext_api.post("/api/v1/services", status_code=HTTPStatus.CREATED)
async def api_create_service(
    data: CreateExternalService,
    user: User = Depends(check_user_exists),
):
    inventory = await get_inventory(user.id, data.inventory_id)
    if not inventory or inventory.user_id != user.id:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail="Cannot create external service.",
        )
    return await create_external_service(data)


@inventory_ext_api.put("/api/v1/services/{service_id}", status_code=HTTPStatus.OK)
async def api_update_service(
    service_id: str,
    data: ExternalService,
    user: User = Depends(check_user_exists),
):
    service = await get_external_service(service_id)
    if not service:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail="External service not found.",
        )
    inventory = await get_inventory(user.id, service.inventory_id)
    if not inventory or inventory.user_id != user.id:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail="Cannot update external service.",
        )
    for field, value in data.dict().items():
        setattr(service, field, value)
    return await update_external_service(service)


@inventory_ext_api.get("/api/v1/services/{inventory_id}", status_code=HTTPStatus.OK)
async def api_get_services(
    inventory_id: str,
    user: User = Depends(check_user_exists),
):
    inventory = await get_inventory(user.id, inventory_id)
    if not inventory or inventory.user_id != user.id:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail="Cannot access external services.",
        )
    return await get_external_services()


@inventory_ext_api.delete(
    "/api/v1/services/{service_id}", status_code=HTTPStatus.NO_CONTENT
)
async def api_delete_service(
    service_id: str,
    user: User = Depends(check_user_exists),
):
    service = await get_external_service(service_id)
    if not service:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail="External service not found.",
        )
    inventory = await get_inventory(user.id, service.inventory_id)
    if not inventory or inventory.user_id != user.id:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail="Cannot delete external service.",
        )
    await delete_external_service(service_id)


# STOCK LOGS
@inventory_ext_api.get(
    "/api/v1/logs/{inventory_id}/paginated",
    openapi_extra=generate_filter_params_openapi(InventoryLogFilters),
    response_model=Page,
)
async def api_get_inventory_logs(
    inventory_id: str,
    user: User = Depends(check_user_exists),
    filters: Filters = Depends(parse_filters(InventoryLogFilters)),
) -> Page:
    inventory = await get_inventory(user.id, inventory_id)
    if not inventory or inventory.user_id != user.id:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail="Inventory not found.",
        )

    page = await get_inventory_update_logs_paginated(inventory_id, filters)
    return page


# Webhook
bearer_scheme = HTTPBearer()


@inventory_ext_api.post("/api/v1/webhooks/stock-update", status_code=HTTPStatus.CREATED)
async def api_webhook_stock_update(
    data: WebhookPayload,
    auth: HTTPAuthorizationCredentials = Depends(bearer_scheme),
):
    if not auth.credentials:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED, detail="No API key provided."
        )
    payload = extract_token_payload(auth.credentials)

    external_service = await get_external_service(payload["service_id"])
    if not external_service:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail="External service not found.",
        )
    if not external_service.is_active:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail="External service is inactive.",
        )

    # check if idempotency key has been used
    if await check_idempotency(data.idempotency_key):
        return {"detail": "Request already processed."}

    # Process stock updates
    item_ids = [item.item_id for item in data.items]
    existing_items = await get_items_by_ids(data.inventory_id, item_ids)

    if external_service.tags:
        allowed_tags = external_service.tags.split(",")
        for item in existing_items:
            if not check_item_tags(
                allowed_tags if external_service.tags else [],
                item.tags.split(",") if item.tags else [],
            ):
                raise HTTPException(
                    status_code=HTTPStatus.FORBIDDEN,
                    detail=f"Item {item.id} has tags not allowed by the external service.",
                )

    for item_data in data.items:
        item = next((i for i in existing_items if i.id == item_data.item_id), None)
        if not item:
            continue  # skip non-existing items

        quantity_before = item.quantity_in_stock or 0
        quantity_after = quantity_before - item_data.quantity_change
        quantity_change = item_data.quantity_change

        # Update item stock
        item.quantity_in_stock = quantity_after
        await update_item(item)

        inventory_log = CreateInventoryUpdateLog(
            inventory_id=data.inventory_id,
            item_id=item.id,
            quantity_change=-quantity_change,
            quantity_before=quantity_before,
            quantity_after=quantity_after,
            source=UpdateSource.WEBHOOK,
            external_service_id=external_service.id,
            idempotency_key=data.idempotency_key,
        )

        # Log the update
        await create_inventory_update_log(inventory_log)
        await update_external_service(external_service)
