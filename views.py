from http import HTTPStatus

from fastapi import APIRouter, Depends, Request
from fastapi.exceptions import HTTPException
from fastapi.responses import HTMLResponse
from lnbits.core.models import User
from lnbits.decorators import check_user_exists
from lnbits.helpers import template_renderer

from .crud import get_manager, get_public_inventory

inventory_ext_generic = APIRouter(tags=["inventory"])


def inventory_renderer():
    return template_renderer(["inventory/templates"])


@inventory_ext_generic.get("/", response_class=HTMLResponse)
async def index(
    request: Request,
    user: User = Depends(check_user_exists),
):
    return inventory_renderer().TemplateResponse(
        request, "inventory/index.html", {"user": user.json()}
    )


@inventory_ext_generic.get("/manager", response_class=HTMLResponse)
async def manager(
    request: Request,
    manager_id: str,
):
    manager = await get_manager(manager_id)
    if not manager:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="Manager not found"
        )
    inventory = await get_public_inventory(manager.inventory_id)
    if not inventory or inventory.id != manager.inventory_id:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="Inventory not found"
        )

    return inventory_renderer().TemplateResponse(
        request,
        "inventory/manager.html",
        {
            "manager": manager.json(),
            "inventory": inventory.json(),
            "user": None,
        },
    )
