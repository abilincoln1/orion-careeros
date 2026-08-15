"""create job discovery schema (lean MVP)

Revision ID: b4e7c9a1f3d2
Revises: 9c1e4f6a2b7d
Create Date: 2026-08-14 00:00:00.000000

JobProvider + JobListing only, per
docs/LEAN-JOB-DISCOVERY-IMPLEMENTATION-PLAN.md. No relationship to
Career DNA tables at all. Follows the same enum-type-handling and
downgrade pattern the career_dna and document_intelligence migrations
established: PostgreSQL-only DROP TYPE on downgrade, no-op on SQLite
(this project's tests create schema via Base.metadata.create_all(),
never by running Alembic migrations).

NOTE: not yet verified against a live PostgreSQL instance in this
session -- verified via SQLAlchemy's Base.metadata.create_all() against
SQLite. Real PostgreSQL verification happens on the project owner's
machine, per this project's established discipline.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'b4e7c9a1f3d2'
down_revision: Union[str, None] = '9c1e4f6a2b7d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Idempotent, checkfirst=True (safe to re-run on partial-failure
    # recovery -- see this migration's own incident history in
    # docs/JOB-DISCOVERY-COMPLETION-REPORT.md). Named job_salary_period,
    # NOT salary_period -- the latter already exists for
    # SalaryPreference.period (annual/monthly/hourly/daily_rate) and is
    # a genuinely different concept; a real naming collision here (an
    # earlier version of this migration) was caught only because
    # PostgreSQL's "type already exists" error surfaced it loudly.
    job_salary_period_enum = postgresql.ENUM(
        'yearly', 'daily', 'hourly', name='job_salary_period'
    )
    job_salary_period_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        'job_provider',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
    )

    op.create_table(
        'job_listing',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('provider_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('provider_external_id', sa.String(length=255), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('company_name_raw', sa.String(length=500), nullable=False),
        sa.Column('location_raw', sa.String(length=500), nullable=True),
        sa.Column('is_remote', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('salary_min', sa.Float(), nullable=True),
        sa.Column('salary_max', sa.Float(), nullable=True),
        sa.Column('salary_currency', sa.String(length=3), nullable=True),
        sa.Column(
            'salary_period',
            postgresql.ENUM('yearly', 'daily', 'hourly', name='job_salary_period', create_type=False),
            nullable=True,
        ),
        sa.Column('salary_disclosed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('description_raw', sa.Text(), nullable=True),
        sa.Column('source_url', sa.String(length=1000), nullable=False),
        sa.Column('posted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('discovered_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('raw_payload_json', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['provider_id'], ['job_provider.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('provider_id', 'provider_external_id', name='ux_job_listing_provider_external_id'),
    )
    op.create_index(op.f('ix_job_listing_provider_id'), 'job_listing', ['provider_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_job_listing_provider_id'), table_name='job_listing')
    op.drop_table('job_listing')
    op.drop_table('job_provider')

    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("DROP TYPE IF EXISTS job_salary_period")
