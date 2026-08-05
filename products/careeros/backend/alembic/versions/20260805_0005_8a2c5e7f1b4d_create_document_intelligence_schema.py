"""create document intelligence schema

Revision ID: 8a2c5e7f1b4d
Revises: 7f4a1b2c9d3e
Create Date: 2026-08-05 00:05:00.000000

Creates Document, DocumentVersion, DocumentExtractionRun -- Phase 2/3
of Sprint 3 Stage 1. See docs/DOCUMENT-INTELLIGENCE-ARCHITECTURE.md and
ADR 0006 for the full design.

Written by hand following the exact enum-type-handling and downgrade
pattern the career_dna migration (6d309ce6ef33) established and
verified: PostgreSQL's `sa.Enum(...)` implicitly emits CREATE TYPE on
upgrade but Alembic's autogenerate does not emit matching DROP TYPE
statements on downgrade -- handled explicitly below, guarded to
PostgreSQL only (see that migration's own docstring for the SQLite
distinction, which applies identically here).

NOTE: not yet verified against a live PostgreSQL instance in this
session (no PostgreSQL available in this sandbox). Verified so far only
via SQLAlchemy's `Base.metadata.create_all()` against SQLite (this
project's test path) -- see docs/SPRINT-3-STAGE1-TEST-STRATEGY.md for
what still needs confirming on real infrastructure before Stage 1 is
considered done.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '8a2c5e7f1b4d'
down_revision: Union[str, None] = '7f4a1b2c9d3e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_ENUM_TYPE_NAMES = ["document_type", "document_status", "document_extraction_run_status"]


def upgrade() -> None:
    op.create_table(
        'document',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('person_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            'document_type',
            sa.Enum('pdf', 'docx', name='document_type'),
            nullable=False,
        ),
        sa.Column(
            'status',
            sa.Enum('uploaded', 'extracted', 'validated', 'imported', 'archived', name='document_status'),
            nullable=False,
            server_default='uploaded',
        ),
        sa.Column('archived_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['person_id'], ['person.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_document_person_id'), 'document', ['person_id'], unique=False)

    op.create_table(
        'document_version',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('version_number', sa.Integer(), nullable=False),
        sa.Column('storage_ref', sa.String(length=500), nullable=False),
        sa.Column('original_filename', sa.String(length=255), nullable=False),
        sa.Column('mime_type', sa.String(length=100), nullable=False),
        sa.Column('size_bytes', sa.Integer(), nullable=False),
        sa.Column('checksum', sa.String(length=64), nullable=False),
        sa.Column('is_current', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('uploaded_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['document_id'], ['document.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('document_id', 'version_number', name='ux_document_version_number'),
    )
    op.create_index(op.f('ix_document_version_document_id'), 'document_version', ['document_id'], unique=False)
    op.create_index(op.f('ix_document_version_checksum'), 'document_version', ['checksum'], unique=False)

    op.create_table(
        'document_extraction_run',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('document_version_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('provider_name', sa.String(length=100), nullable=False),
        sa.Column('run_number', sa.Integer(), nullable=False),
        sa.Column(
            'status',
            sa.Enum('pending', 'completed', 'failed', name='document_extraction_run_status'),
            nullable=False,
            server_default='pending',
        ),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('overall_confidence', sa.Float(), nullable=True),
        sa.Column('raw_extraction_json', sa.JSON(), nullable=True),
        sa.Column('error_detail', sa.Text(), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('reviewed_by_person_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('applied_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['document_version_id'], ['document_version.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['reviewed_by_person_id'], ['person.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint(
            'document_version_id', 'provider_name', 'run_number',
            name='ux_document_extraction_run_number',
        ),
    )
    op.create_index(
        op.f('ix_document_extraction_run_document_version_id'),
        'document_extraction_run', ['document_version_id'], unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f('ix_document_extraction_run_document_version_id'), table_name='document_extraction_run'
    )
    op.drop_table('document_extraction_run')
    op.drop_index(op.f('ix_document_version_checksum'), table_name='document_version')
    op.drop_index(op.f('ix_document_version_document_id'), table_name='document_version')
    op.drop_table('document_version')
    op.drop_index(op.f('ix_document_person_id'), table_name='document')
    op.drop_table('document')

    # Hand-added, matching the career_dna migration's established
    # pattern: PostgreSQL-only, drop every enum type this migration
    # created. On SQLite these are plain VARCHAR+CHECK columns dropped
    # automatically with their table.
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        for type_name in _ENUM_TYPE_NAMES:
            op.execute(f"DROP TYPE IF EXISTS {type_name}")
