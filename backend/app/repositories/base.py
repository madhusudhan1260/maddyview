"""Generic repository for user-owned rows. Every query is scoped by user_id and uses bound parameters."""

from collections.abc import Sequence
from typing import Any, Generic, TypeVar

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.core.errors import NotFoundError
from app.database.base import Base
from app.models.enums import DataSource

M = TypeVar("M", bound=Base)


def visible_sources(include_demo: bool) -> list[DataSource]:
    """Which data-source labels a query may return given the user's DEMO toggle."""
    return list(DataSource) if include_demo else [s for s in DataSource if s != DataSource.DEMO]


class OwnedRepository(Generic[M]):
    def __init__(self, model: type[M], label: str):
        self.model = model
        self.label = label

    def query(self, user_id: int, include_demo: bool = True) -> Select:
        stmt = select(self.model).where(self.model.user_id == user_id)
        if hasattr(self.model, "source"):
            stmt = stmt.where(self.model.source.in_(visible_sources(include_demo)))
        return stmt

    def list(self, db: Session, user_id: int, *, include_demo: bool = True, filters: Sequence = (), order_by: Sequence = ()) -> list[M]:
        stmt = self.query(user_id, include_demo)
        for f in filters:
            stmt = stmt.where(f)
        if order_by:
            stmt = stmt.order_by(*order_by)
        return list(db.scalars(stmt))

    def get(self, db: Session, user_id: int, obj_id: int) -> M:
        obj = db.scalar(select(self.model).where(self.model.id == obj_id, self.model.user_id == user_id))
        if obj is None:
            raise NotFoundError(f"{self.label} not found")
        return obj

    def create(self, db: Session, user_id: int, data: dict[str, Any]) -> M:
        obj = self.model(user_id=user_id, **data)
        db.add(obj)
        db.flush()
        return obj

    def update(self, db: Session, obj: M, changes: dict[str, Any]) -> M:
        for key, value in changes.items():
            setattr(obj, key, value)
        db.flush()
        return obj

    def delete(self, db: Session, obj: M) -> None:
        db.delete(obj)
        db.flush()
