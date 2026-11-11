"""Factory for the standard owned-resource CRUD endpoints (list/create/get/patch/delete) with auditing."""

from collections.abc import Callable

from fastapi import APIRouter, Response, status
from pydantic import BaseModel

from app.api.deps import Ctx, CurrentCtx
from app.models.enums import DataSource
from app.repositories.base import OwnedRepository
from app.services import audit


def crud_router(
    *,
    path: str,
    tag: str,
    repo: OwnedRepository,
    create_schema: type[BaseModel],
    update_schema: type[BaseModel],
    out_schema: type[BaseModel],
    entity: str,
    view: Callable[[Ctx, object], object] = lambda ctx, obj: obj,
    validate: Callable[[Ctx, dict, object | None], dict] = lambda ctx, data, obj: data,
    include_list: bool = True,
    list_order=None,
) -> APIRouter:
    router = APIRouter(prefix=path, tags=[tag])

    if include_list:
        @router.get("", response_model=list[out_schema], name=f"list_{entity}")
        def list_items(ctx: CurrentCtx):
            order = list_order(repo.model) if list_order else [repo.model.id.desc()]
            return [view(ctx, o) for o in repo.list(ctx.db, ctx.user.id, include_demo=ctx.include_demo, order_by=order)]

    @router.post("", response_model=out_schema, status_code=status.HTTP_201_CREATED, name=f"create_{entity}")
    def create_item(body: create_schema, ctx: CurrentCtx):  # type: ignore[valid-type]
        data = validate(ctx, body.model_dump(), None)
        obj = repo.create(ctx.db, ctx.user.id, {**data, "source": DataSource.USER_ENTERED})
        audit.record(ctx.db, f"{entity}.create", user_id=ctx.user.id, entity_type=entity, entity_id=obj.id, ip=ctx.ip)
        ctx.db.commit()
        return view(ctx, obj)

    @router.get("/{item_id}", response_model=out_schema, name=f"get_{entity}")
    def get_item(item_id: int, ctx: CurrentCtx):
        return view(ctx, repo.get(ctx.db, ctx.user.id, item_id))

    @router.patch("/{item_id}", response_model=out_schema, name=f"update_{entity}")
    def update_item(item_id: int, body: update_schema, ctx: CurrentCtx):  # type: ignore[valid-type]
        obj = repo.get(ctx.db, ctx.user.id, item_id)
        changes = validate(ctx, body.model_dump(exclude_unset=True), obj)
        repo.update(ctx.db, obj, changes)
        audit.record(ctx.db, f"{entity}.update", user_id=ctx.user.id, entity_type=entity, entity_id=obj.id,
                     details={"fields": sorted(changes)}, ip=ctx.ip)
        ctx.db.commit()
        ctx.db.refresh(obj)
        return view(ctx, obj)

    @router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT, name=f"delete_{entity}")
    def delete_item(item_id: int, ctx: CurrentCtx):
        obj = repo.get(ctx.db, ctx.user.id, item_id)
        repo.delete(ctx.db, obj)
        audit.record(ctx.db, f"{entity}.delete", user_id=ctx.user.id, entity_type=entity, entity_id=item_id, ip=ctx.ip)
        ctx.db.commit()
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    return router
