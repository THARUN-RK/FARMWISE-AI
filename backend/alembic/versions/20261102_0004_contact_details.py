"""Add persistent contact details for farmers and buyers."""

from alembic import op
import sqlalchemy as sa

revision = "20261102_0004"
down_revision = "20261101_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())

    if "contact_details" not in existing_tables:
        op.create_table(
            "contact_details",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("farmer_id", sa.Integer(), nullable=True),
            sa.Column("buyer_id", sa.Integer(), nullable=True),
            sa.Column("phone", sa.String(length=20), nullable=True),
            sa.Column("alternate_phone", sa.String(length=20), nullable=True),
            sa.Column("email", sa.String(length=255), nullable=True),
            sa.Column("whatsapp", sa.String(length=20), nullable=True),
            sa.Column("address_line1", sa.String(length=200), nullable=True),
            sa.Column("address_line2", sa.String(length=200), nullable=True),
            sa.Column("city", sa.String(length=120), nullable=True),
            sa.Column("district", sa.String(length=120), nullable=True),
            sa.Column("state", sa.String(length=120), nullable=True),
            sa.Column("pincode", sa.String(length=12), nullable=True),
            sa.Column("preferred_contact_method", sa.String(length=20), nullable=False, server_default="phone"),
            sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.ForeignKeyConstraint(["farmer_id"], ["farmers.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["buyer_id"], ["buyers.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("farmer_id", "is_primary", name="uq_contact_details_farmer_primary"),
            sa.UniqueConstraint("buyer_id", "is_primary", name="uq_contact_details_buyer_primary"),
        )
        op.create_index("ix_contact_details_farmer_id", "contact_details", ["farmer_id"], unique=False)
        op.create_index("ix_contact_details_buyer_id", "contact_details", ["buyer_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_contact_details_buyer_id"), table_name="contact_details")
    op.drop_index(op.f("ix_contact_details_farmer_id"), table_name="contact_details")
    op.drop_table("contact_details")
