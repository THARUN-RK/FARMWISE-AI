"""Add Google profile metadata and OTP verification storage."""

from alembic import op
import sqlalchemy as sa

revision = "20261101_0002"
down_revision = "20261031_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if "farmers" in inspector.get_table_names():
        existing_columns = {column["name"] for column in inspector.get_columns("farmers")}
        if "google_id" not in existing_columns:
            op.add_column("farmers", sa.Column("google_id", sa.String(length=255), nullable=True))
        if "profile_picture" not in existing_columns:
            op.add_column("farmers", sa.Column("profile_picture", sa.String(length=512), nullable=True))
        if "mobile_number" not in existing_columns:
            op.add_column("farmers", sa.Column("mobile_number", sa.String(length=20), nullable=True))
        if "email_verified" not in existing_columns:
            op.add_column("farmers", sa.Column("email_verified", sa.Boolean(), nullable=False, server_default=sa.false()))
        if "last_login" not in existing_columns:
            op.add_column("farmers", sa.Column("last_login", sa.DateTime(), nullable=True))
        if "account_status" not in existing_columns:
            op.add_column("farmers", sa.Column("account_status", sa.String(length=30), nullable=False, server_default="active"))

    if "email_otps" not in inspector.get_table_names():
        op.create_table(
            "email_otps",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("farmer_id", sa.Integer(), sa.ForeignKey("farmers.id", ondelete="CASCADE"), nullable=False),
            sa.Column("purpose", sa.String(length=30), nullable=False, server_default="google_login"),
            sa.Column("code_hash", sa.String(length=128), nullable=False),
            sa.Column("expires_at", sa.DateTime(), nullable=False),
            sa.Column("used_at", sa.DateTime(), nullable=True),
            sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        )
        op.create_index(op.f("ix_email_otps_farmer_id"), "email_otps", ["farmer_id"], unique=False)
        op.create_index(op.f("ix_email_otps_purpose"), "email_otps", ["purpose"], unique=False)
        op.create_index(op.f("ix_email_otps_code_hash"), "email_otps", ["code_hash"], unique=False)
        op.create_index(op.f("ix_email_otps_expires_at"), "email_otps", ["expires_at"], unique=False)

    if "farmers" in inspector.get_table_names():
        op.create_index(op.f("ix_farmers_google_id"), "farmers", ["google_id"], unique=True, if_not_exists=True)
        op.create_index(op.f("ix_farmers_mobile_number"), "farmers", ["mobile_number"], unique=True, if_not_exists=True)
        op.create_index(op.f("ix_farmers_account_status"), "farmers", ["account_status"], unique=False, if_not_exists=True)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "email_otps" in inspector.get_table_names():
        op.drop_table("email_otps")
    for column_name in ["google_id", "profile_picture", "mobile_number", "email_verified", "last_login", "account_status"]:
        if "farmers" in inspector.get_table_names() and column_name in {column["name"] for column in inspector.get_columns("farmers")}:
            op.drop_column("farmers", column_name)
