from pathlib import Path
from types import SimpleNamespace

import httpx
import pytest
import pytest_asyncio
from fastapi import FastAPI, HTTPException, Request
from lnbits import db as database_module
from lnbits.db import Database
from lnbits.settings import settings

from .. import crud, inventory_ext, migrations, views_api
from ..models import Inventory, Item

QUANTITIES_URL = "/inventory/api/v1/items/catalog/quantities"
QUOTED_ID = "shopkeeper's-item"


@pytest_asyncio.fixture
async def inventory_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(settings, "lnbits_data_folder", str(tmp_path))
    monkeypatch.setattr(database_module, "DB_TYPE", database_module.SQLITE)
    db = Database("ext_inventory")
    monkeypatch.setattr(crud, "db", db)
    try:
        await migrations.m001_initial(db)
        await migrations.m002_add_item_weight(db)
        for inventory_id, user_id in (("catalog", "owner"), ("other", "nonowner")):
            await db.insert(
                "inventory.inventories",
                Inventory(
                    id=inventory_id, user_id=user_id, name="Shop", currency="USD"
                ),
            )
        for item_id, inventory_id, stock in (
            ("regular", "catalog", 5),
            (QUOTED_ID, "catalog", 2),
            ("untracked", "catalog", None),
            ("unchanged", "catalog", 6),
            ("foreign", "other", 9),
        ):
            await db.insert(
                "inventory.items",
                Item(
                    id=item_id,
                    inventory_id=inventory_id,
                    name="Stock item",
                    price=1,
                    is_active=True,
                    quantity_in_stock=stock,
                ),
            )
        yield db
    finally:
        await db.engine.dispose()


@pytest_asyncio.fixture
async def client(inventory_db: Database):
    def check_test_user(request: Request) -> SimpleNamespace:
        user_id = request.headers.get("x-test-user")
        if user_id not in ("owner", "nonowner"):
            raise HTTPException(401, "Authentication required")
        return SimpleNamespace(id=user_id)

    app = FastAPI()
    app.include_router(inventory_ext)
    app.dependency_overrides[views_api.check_user_exists] = check_test_user
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client


@pytest.mark.asyncio
async def test_get_items_by_ids(inventory_db: Database):
    assert await crud.get_items_by_ids("catalog", []) == []
    assert await crud.get_items_by_ids("catalog", "") == []
    items = await crud.get_items_by_ids("catalog", QUOTED_ID)
    assert [item.id for item in items] == [QUOTED_ID]
    items = await crud.get_items_by_ids(
        "catalog", [QUOTED_ID, "regular", "missing", "foreign", "regular"]
    )
    assert sorted(item.id for item in items) == ["regular", QUOTED_ID]


@pytest.mark.asyncio
async def test_bulk_stock_updates_only_matching_tracked_items(
    client: httpx.AsyncClient,
):
    response = await client.patch(
        QUANTITIES_URL,
        headers={"x-test-user": "owner"},
        params={
            "source": "tpos",
            "ids": [
                "regular",
                QUOTED_ID,
                "untracked",
                "unchanged",
                "missing",
                "foreign",
            ],
            "quantities": [3, 9, 1, 0, 1, 1],
        },
    )
    assert response.status_code == 200
    assert [(item["id"], item["quantity_in_stock"]) for item in response.json()] == [
        ("regular", 2),
        (QUOTED_ID, 0),
    ]
    catalog = await crud.get_inventory_items("catalog")
    assert {item.id: item.quantity_in_stock for item in catalog} == {
        "regular": 2,
        QUOTED_ID: 0,
        "untracked": None,
        "unchanged": 6,
    }
    foreign = await crud.get_item("foreign")
    assert foreign is not None and foreign.quantity_in_stock == 9
    audit = await crud.get_inventory_update_logs_paginated("catalog")
    assert audit.total == 2
    assert {
        (row.item_id, row.quantity_before, row.quantity_after, row.quantity_change)
        for row in audit.data
    } == {("regular", 5, 2, -3), (QUOTED_ID, 2, 0, -2)}
    assert all(row.source == "tpos" for row in audit.data)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("user_id", "quantities", "expected_status"),
    [(None, [1], 401), ("nonowner", [1], 404), ("owner", [1, 2], 400)],
)
async def test_bulk_stock_rejects_unauthorized_or_mismatched_requests(
    client: httpx.AsyncClient,
    user_id: str | None,
    quantities: list[int],
    expected_status: int,
):
    response = await client.patch(
        QUANTITIES_URL,
        headers={"x-test-user": user_id} if user_id else {},
        params={"ids": ["regular"], "quantities": quantities},
    )
    assert response.status_code == expected_status
    item = await crud.get_item("regular")
    assert item is not None and item.quantity_in_stock == 5
    assert (await crud.get_inventory_update_logs_paginated("catalog")).total == 0
