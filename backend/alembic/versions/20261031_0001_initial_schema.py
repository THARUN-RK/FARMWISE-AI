"""Baseline the current schema for empty and existing installations.

The previous application initialized tables with create_all() before Alembic
existed. This baseline therefore creates missing tables only, so it can run on
both an empty database and a legacy database without dropping farmer data.
"""
from alembic import op
from sqlalchemy import Column, String, inspect

from app.core.database import Base
from app.models import entities  # noqa: F401 - register all mapped tables

revision = "20261031_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    existing_tables = set(inspector.get_table_names())

    # The legacy production SQLite/PostgreSQL schema can predate these profile
    # fields. Add them before Alembic takes over schema changes.
    if "farmers" in existing_tables:
        existing_columns = {column["name"] for column in inspector.get_columns("farmers")}
        if "state" not in existing_columns:
            op.add_column("farmers", Column("state", String(80), nullable=True))
        if "district" not in existing_columns:
            op.add_column("farmers", Column("district", String(80), nullable=True))

    # Create each absent table in FK dependency order. Existing tables and their
    # data are preserved; create() also adds the table's declared indexes.
    for table in Base.metadata.sorted_tables:
        if table.name not in existing_tables:
            table.create(bind=bind, checkfirst=True)
            existing_tables.add(table.name)


def downgrade() -> None:
    # This baseline also adopts legacy user data, so it cannot be safely rolled
    # back automatically. Future revisions should provide reversible downgrades.
    raise RuntimeError("The initial schema baseline is irreversible; restore a database backup instead.")
