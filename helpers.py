from .models import CreateItem, ImportItem, Manager


def check_item_tags(service_allowed_tags: list[str], item_tags: list[str]) -> bool:
    if service_allowed_tags == []:
        return True
    return any(tag in service_allowed_tags for tag in item_tags)


def split_tags(tags: str | None) -> list[str]:
    if not tags:
        return []
    return [tag.strip() for tag in tags.split(",") if tag.strip()]


def to_csv(value: list[str] | str | None) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        cleaned = value.strip()
        return cleaned or None
    cleaned_values = [str(item).strip() for item in value if str(item).strip()]
    return ",".join(cleaned_values) if cleaned_values else None


def from_csv(value: str | None, separator: str = ",") -> list[str]:
    if not value:
        return []
    parts = [part.strip() for part in value.split(separator)]
    return [part for part in parts if part]


def normalize_images(value: str | list[str] | None) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    separator = "|||" if "|||" in value else ","
    return from_csv(value, separator=separator)


def to_images_csv(value: list[str] | str | None) -> str | None:
    if value is None:
        return None
    if isinstance(value, list):
        cleaned = [str(v).strip() for v in value if str(v).strip()]
        return "|||".join(cleaned) if cleaned else None
    cleaned_str = str(value).strip()
    return cleaned_str or None


def prepare_import_item(item: ImportItem, inventory_id: str) -> CreateItem:
    return CreateItem(
        inventory_id=inventory_id,
        name=item.name,
        description=item.description,
        images=to_images_csv(item.images),
        sku=item.sku,
        quantity_in_stock=item.quantity_in_stock,
        price=item.price,
        discount_percentage=item.discount_percentage,
        tax_rate=item.tax_rate,
        reorder_threshold=item.reorder_threshold,
        unit_cost=item.unit_cost,
        external_id=item.external_id,
        tags=to_csv(item.tags),
        omit_tags=to_csv(item.omit_tags),
        is_active=item.is_active if item.is_active is not None else True,
        internal_note=item.internal_note,
        manager_id=None,
        is_approved=item.is_approved if item.is_approved is not None else True,
    )


def manager_allowed_tags(manager: Manager) -> list[str] | None:
    if manager.tags is None:
        return None
    return split_tags(manager.tags)


def manager_allows_tags(manager: Manager, item_tags: list[str]) -> bool:
    allowed_tags = manager_allowed_tags(manager)
    if allowed_tags is None:
        return True
    if not allowed_tags:
        return False
    if not item_tags:
        return False
    return all(tag in allowed_tags for tag in item_tags)
