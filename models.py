from datetime import datetime, timezone
from enum import Enum

from fastapi.params import Form
from pydantic import BaseModel, Field, validator

from lnbits.db import FilterModel


class CreateInventory(BaseModel):
    name: str
    currency: str
    global_discount_percentage: float = 0.0
    default_tax_rate: float = 0.0
    is_tax_inclusive: bool = True
    tags: str | None = None


class PublicInventory(CreateInventory):
    id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Inventory(PublicInventory):
    user_id: str


class CreateCategory(BaseModel):
    inventory_id: str
    name: str
    description: str | None = None


class Category(CreateCategory):
    id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CreateItem(BaseModel):
    inventory_id: str
    categories: list[Category] = Field(default_factory=list)
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
    is_active: bool = True
    internal_note: str | None = None
    manager_id: str | None = None
    is_approved: bool = True


class PublicItem(BaseModel):
    id: str
    inventory_id: str
    categories: list[Category] = Field(default_factory=list)
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
    __search_fields__ = [
        "name",
        "description",
        "sku",
        "is_active",
        "internal_note",
        "manager_id",
        "tags",
        "is_approved",
    ]

    __sort_fields__ = ["name", "created_at", "price", "quantity_in_stock", "tags"]

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


# External services that can update inventory via API or webhooks
class CreateExternalService(BaseModel):
    service_name: str
    inventory_id: str
    description: str | None = None
    tags: str | None = None


class ExternalService(CreateExternalService):
    id: str
    api_key: str
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_used_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# Inventory update logs
class InventoryUpdateMetadata(BaseModel):
    order_id: int | None = None
    transaction_id: str | None = None
    note: str | None = None


class UpdateSource(str, Enum):
    WEBHOOK = "webhook"
    MANUAL = "manual"
    SYSTEM = "system"


class CreateInventoryUpdateLog(BaseModel):
    inventory_id: str
    item_id: str
    quantity_change: int
    quantity_before: int
    quantity_after: int
    source: UpdateSource = UpdateSource.WEBHOOK
    external_service_id: str | None = None
    idempotency_key: str
    metadata: InventoryUpdateMetadata | None = None


class InventoryUpdateLog(CreateInventoryUpdateLog):
    id: int
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class InventoryLogFilters(FilterModel):
    __search_fields__ = ["external_service_id", "idempotency_key", "item_id"]

    __sort_fields__ = [
        "created_at",
        "item_id",
        "quantity_change",
        "external_service_id",
        "source",
    ]

    external_service_id: str | None = None
    idempotency_key: str | None = None
    item_id: str | None = None
    created_at: datetime | None = None
    source: str | None = None


# Webhook models
class UpdateOperation(str, Enum):
    ADD = "add"
    SUBTRACT = "subtract"
    SET = "set"


class InventoryItem(BaseModel):
    item_id: str
    quantity_change: int
    operation: UpdateOperation = UpdateOperation.SUBTRACT


class WebhookPayload(BaseModel):
    """Webhook payload for inventory updates"""

    inventory_id: str
    items: list[InventoryItem]
    timestamp: datetime
    idempotency_key: str = Field(..., min_length=16, max_length=128)

    @validator("timestamp")
    def validate_timestamp(cls, v):
        """Ensure timestamp is recent (within 5 minutes)"""
        now = datetime.now(timezone.utc)
        time_diff = abs((now - v).total_seconds())

        if time_diff > 300:  # 5 minutes
            raise ValueError("Timestamp too old or in future")
        return v


# create an example body json for the webhook payload
# {
#   "inventory_id": "inv_123456",
#   "items": [
#     {
#       "item_id": "item_123",
#       "quantity_change": 5,
#       "operation": "subtract"
#     },
#     {
#       "item_id": "item_456",
#       "quantity_change": 10,
#       "operation": "add"
#     }
#   ],
#   "timestamp": "",
#   "idempotency_key": "unique_key_1234567890"
# }
