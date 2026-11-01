"""Add crop planner farm profiles and recommendation tables."""

from alembic import op
import sqlalchemy as sa

revision = "20261101_0003"
down_revision = "20261031_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())

    if "farm_profiles" not in existing_tables:
        op.create_table(
            "farm_profiles",
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("state", sa.String(length=80), nullable=True),
            sa.Column("district", sa.String(length=80), nullable=True),
            sa.Column("taluk", sa.String(length=80), nullable=True),
            sa.Column("village", sa.String(length=100), nullable=True),
            sa.Column("land_area_acres", sa.Float(), nullable=True),
            sa.Column("soil_type", sa.String(length=80), nullable=True),
            sa.Column("water_availability", sa.String(length=50), nullable=True),
            sa.Column("irrigation_type", sa.String(length=50), nullable=True),
            sa.Column("current_season", sa.String(length=50), nullable=True),
            sa.Column("budget", sa.Float(), nullable=True),
            sa.Column("previous_crop", sa.String(length=80), nullable=True),
            sa.Column("preferred_crop_category", sa.String(length=80), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.ForeignKeyConstraint(["user_id"], ["farmers.id"], ondelete="CASCADE"),
            sa.UniqueConstraint("user_id", name="uq_farm_profiles_user"),
        )

    if "crops" in existing_tables:
        current_columns = {column["name"] for column in inspector.get_columns("crops")}
        if "crop_category" not in current_columns:
            op.add_column("crops", sa.Column("crop_category", sa.String(length=80), nullable=True))
        if "suitable_regions" not in current_columns:
            op.add_column("crops", sa.Column("suitable_regions", sa.String(length=255), nullable=True))
        if "minimum_land_area" not in current_columns:
            op.add_column("crops", sa.Column("minimum_land_area", sa.Float(), nullable=True))
        if "seed_requirement_per_acre" not in current_columns:
            op.add_column("crops", sa.Column("seed_requirement_per_acre", sa.String(length=120), nullable=True))
        if "fertilizer_guidelines" not in current_columns:
            op.add_column("crops", sa.Column("fertilizer_guidelines", sa.Text(), nullable=True))
        if "estimated_cost_per_acre" not in current_columns:
            op.add_column("crops", sa.Column("estimated_cost_per_acre", sa.Float(), nullable=True))
        if "expected_yield_min" not in current_columns:
            op.add_column("crops", sa.Column("expected_yield_min", sa.Float(), nullable=True))
        if "expected_yield_max" not in current_columns:
            op.add_column("crops", sa.Column("expected_yield_max", sa.Float(), nullable=True))
        if "temperature_range" not in current_columns:
            op.add_column("crops", sa.Column("temperature_range", sa.String(length=80), nullable=True))
        if "rainfall_requirement" not in current_columns:
            op.add_column("crops", sa.Column("rainfall_requirement", sa.String(length=80), nullable=True))
        if "created_at" not in current_columns:
            op.add_column("crops", sa.Column("created_at", sa.DateTime(), nullable=True, server_default=sa.text("CURRENT_TIMESTAMP")))
        if "updated_at" not in current_columns:
            op.add_column("crops", sa.Column("updated_at", sa.DateTime(), nullable=True, server_default=sa.text("CURRENT_TIMESTAMP")))

    if "crop_recommendations" not in existing_tables:
        op.create_table(
            "crop_recommendations",
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("farm_profile_id", sa.Integer(), nullable=True),
            sa.Column("crop_id", sa.Integer(), nullable=True),
            sa.Column("crop_name", sa.String(length=80), nullable=False),
            sa.Column("suitability_score", sa.Float(), nullable=False, server_default="0"),
            sa.Column("suitability_category", sa.String(length=20), nullable=False, server_default="Low"),
            sa.Column("cultivation_duration_days", sa.Integer(), nullable=True),
            sa.Column("water_requirement", sa.String(length=40), nullable=True),
            sa.Column("estimated_cost_per_acre", sa.Float(), nullable=True),
            sa.Column("expected_yield", sa.Float(), nullable=True),
            sa.Column("reasons", sa.Text(), nullable=True),
            sa.Column("risks", sa.Text(), nullable=True),
            sa.Column("data_sources", sa.Text(), nullable=True),
            sa.Column("generated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.ForeignKeyConstraint(["user_id"], ["farmers.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["farm_profile_id"], ["farm_profiles.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["crop_id"], ["crops.id"], ondelete="SET NULL"),
        )
        op.create_index("ix_crop_recommendations_user_generated", "crop_recommendations", ["user_id", "generated_at"], unique=False)

    if "saved_crop_recommendations" not in existing_tables:
        op.create_table(
            "saved_crop_recommendations",
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("recommendation_id", sa.Integer(), nullable=False),
            sa.Column("saved_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.ForeignKeyConstraint(["user_id"], ["farmers.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["recommendation_id"], ["crop_recommendations.id"], ondelete="CASCADE"),
            sa.UniqueConstraint("user_id", "recommendation_id", name="uq_saved_crop_recommendation_user"),
        )


def downgrade() -> None:
    op.drop_table("saved_crop_recommendations")
    op.drop_table("crop_recommendations")
    op.drop_table("farm_profiles")
