"""TD-023 Option B: add attribution_source to employment

Revision ID: 9c1e4f6a2b7d
Revises: 8a2c5e7f1b4d
Create Date: 2026-08-13 12:30:00.000000

Adds attribution_source to Employment, mirroring the existing column on
PersonSkill/PersonCompetency/PersonTechnology exactly (same enum, same
default). This is the narrow TD-023 Option B fix -- Employment-only,
no new table, no repository-wide provenance migration. See
docs/TD-023-RESOLUTION-REPORT.md Section 2 (Option B) and the MVP
Priority 1 authorisation.

Backward compatible: NOT NULL with a server_default, so existing
Employment rows (if any) are automatically backfilled to
'self_reported' -- accurate, since every Employment row created before
this migration was necessarily user-entered (no other write path
existed).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '9c1e4f6a2b7d'
down_revision: Union[str, None] = '8a2c5e7f1b4d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'employment',
        sa.Column(
            'attribution_source',
            sa.Enum(
                'self_reported', 'inferred', 'verified', 'ai_extracted', 'imported',
                name='attribution_source',
                # The enum type already exists (created for PersonSkill in
                # 6d309ce6ef33, extended in 7f4a1b2c9d3e) -- do not
                # attempt to recreate it.
                create_type=False,
            ),
            nullable=False,
            server_default='self_reported',
        ),
    )


def downgrade() -> None:
    op.drop_column('employment', 'attribution_source')
