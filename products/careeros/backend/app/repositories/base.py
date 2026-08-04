"""
Generic async repository base.

Career DNA has ~27 entities; most CRUD is structurally identical (get by
id, list with pagination, create, update, delete). This base class
implements that once so each entity's repository is a thin subclass that
only adds what's actually different for it -- filtering, dedup, whatever
is entity-specific. This is a repository-layer analogue of the same
"don't repeat a pattern 27 times" reasoning behind
app/models/mixins.py.
"""
import uuid
from typing import Any, Generic, Optional, Sequence, Type, TypeVar

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType], db: AsyncSession):
        self.model = model
        self.db = db

    async def get(self, id_: uuid.UUID) -> Optional[ModelType]:
        return await self.db.get(self.model, id_)

    async def list(
        self,
        *,
        offset: int = 0,
        limit: int = 50,
        filters: Optional[dict[str, Any]] = None,
        order_by: Optional[Any] = None,
    ) -> tuple[Sequence[ModelType], int]:
        """Returns (rows, total_count) -- total_count ignores offset/limit,
        for building paginated response envelopes."""
        stmt = select(self.model)
        count_stmt = select(func.count()).select_from(self.model)

        for field, value in (filters or {}).items():
            column = getattr(self.model, field)
            stmt = stmt.where(column == value)
            count_stmt = count_stmt.where(column == value)

        if order_by is not None:
            stmt = stmt.order_by(order_by)

        stmt = stmt.offset(offset).limit(limit)

        rows = (await self.db.execute(stmt)).scalars().all()
        total = (await self.db.execute(count_stmt)).scalar_one()
        return rows, total

    async def create(self, obj: ModelType) -> ModelType:
        self.db.add(obj)
        await self.db.flush()
        return obj

    async def delete(self, obj: ModelType) -> None:
        await self.db.delete(obj)
        await self.db.flush()
