from datetime import datetime, timezone

from pydantic import BaseModel, Field

from lnbits.db import FilterModel


class CreateInventory(BaseModel):
    name: str
    currency: str
    global_discount_percentage: float = 0.0
    default_tax_rate: float = 0.0
    is_tax_inclusive: bool = True
    tags: str | None = None
    omit_tags: str | None = None


class PublicInventory(CreateInventory):
    id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Inventory(PublicInventory):
    user_id: str


class CreateItem(BaseModel):
    inventory_id: str
    name: str
    description: str | None = None
    images: str | None = None
    sku: str | None = None
    quantity_in_stock: int | None = None
    price: float
    discount_percentage: float | None = None
    tax_rate: float | None = None
    reorder_threshold: int | None = None
    unit_cost: float | None = None
    external_id: str | None = None
    tags: str | None = None
    omit_tags: str | None = None
    is_active: bool = True
    internal_note: str | None = None
    manager_id: str | None = None
    is_approved: bool = True


class PublicItem(BaseModel):
    id: str
    inventory_id: str
    name: str
    description: str | None = None
    images: str | None = None
    sku: str | None = None
    quantity_in_stock: int | None = None
    price: float
    discount_percentage: float | None
    tax_rate: float | None
    external_id: str | None = None
    tags: str | None = None
    omit_tags: str | None = None
    is_active: bool
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Item(PublicItem):
    external_id: str | None = None
    manager_id: str | None = None
    internal_note: str | None = None
    unit_cost: float | None = None
    reorder_threshold: int | None = None
    is_approved: bool = False


class ItemFilters(FilterModel):
    __search_fields__: list[str] = [  # noqa: RUF012
        "name",
        "description",
        "sku",
        "is_active",
        "internal_note",
        "manager_id",
        "tags",
        "is_approved",
    ]

    __sort_fields__: list[str] | None = [  # noqa: RUF012
        "name",
        "created_at",
        "price",
        "quantity_in_stock",
        "tags",
    ]

    name: str | None = None
    description: str | None = None
    sku: str | None = None
    is_active: bool | None = None
    internal_note: str | None = None
    tags: str | None = None
    manager_id: str | None = None
    is_approved: bool | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


# Inventory owner can assign managers to help manage items and stock
class CreateManager(BaseModel):
    inventory_id: str
    name: str
    email: str | None = None
    tags: str | None = None


class Manager(CreateManager):
    id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ManagerQuantityUpdate(BaseModel):
    inventory_id: str
    quantity_in_stock: int


# Inventory update logs
class InventoryUpdateMetadata(BaseModel):
    order_id: int | None = None
    transaction_id: str | None = None
    note: str | None = None


class CreateInventoryUpdateLog(BaseModel):
    inventory_id: str
    item_id: str
    quantity_change: int
    quantity_before: int
    quantity_after: int
    source: str = "webhook"
    idempotency_key: str
    metadata: InventoryUpdateMetadata | None = None


class InventoryUpdateLog(CreateInventoryUpdateLog):
    id: int
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class InventoryLogFilters(FilterModel):
    __search_fields__: list[str] = ["idempotency_key", "item_id"]  # noqa: RUF012

    __sort_fields__: list[str] | None = [  # noqa: RUF012
        "created_at",
        "item_id",
        "quantity_change",
        "source",
    ]

    idempotency_key: str | None = None
    item_id: str | None = None
    created_at: datetime | None = None
    source: str | None = None


class ImportItem(BaseModel):
    name: str
    price: float
    description: str | None = None
    images: list[str] | str | None = None
    sku: str | None = None
    quantity_in_stock: int | None = None
    discount_percentage: float | None = None
    tax_rate: float | None = None
    reorder_threshold: int | None = None
    unit_cost: float | None = None
    external_id: str | None = None
    tags: list[str] | str | None = None
    omit_tags: list[str] | str | None = None
    is_active: bool | None = True
    internal_note: str | None = None
    manager_id: str | None = None
    is_approved: bool | None = True

    class Config:
        extra = "ignore"


class ImportItemsPayload(BaseModel):
    items: list[ImportItem]
