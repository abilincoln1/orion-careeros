"""
Career DNA Service: shared model mixins.

Every Career DNA table has a UUID primary key and created_at/updated_at
timestamps, following the same pattern Sprint 1's `User` model already
established. Factored out here so that pattern is defined once instead
of repeated (and potentially drifting) across ~30 model classes.
"""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column


def db_enum(enum_cls, name: str):
    """
    Build a SQLAlchemy Enum column type that stores/reads the Python
    enum's `.value` (e.g. "self_reported"), not its member `.name`
    (e.g. "SELF_REPORTED") -- SQLAlchemy's default behavior for a PEP435
    enum class. Found via a real `create_all()` run against embedded
    PostgreSQL during Sprint 2 verification: without `values_callable`,
    the generated PostgreSQL enum type only accepted upper-cased member
    names, which didn't match this codebase's lower_snake_case
    `server_default` values (and would not have matched Pydantic/JSON API
    serialization either, which uses `.value` throughout). Used by every
    Career DNA model instead of calling `sqlalchemy.Enum(...)` directly,
    so this fix applies uniformly rather than needing to be repeated (and
    potentially missed) at every one of the ~25 enum columns in this
    schema.
    """
    return SAEnum(enum_cls, name=name, values_callable=lambda obj: [e.value for e in obj])


class UUIDPrimaryKeyMixin:
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
