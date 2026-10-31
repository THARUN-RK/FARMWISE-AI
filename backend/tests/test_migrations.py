import os
import sqlite3
import subprocess
import sys
from pathlib import Path

from sqlalchemy import create_engine, inspect

BACKEND_DIR = Path(__file__).resolve().parents[1]


def test_baseline_adopts_legacy_sqlite_schema_without_losing_farmer_data(tmp_path):
    database_path = tmp_path / "legacy.sqlite"
    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """CREATE TABLE farmers (
                id INTEGER PRIMARY KEY,
                name VARCHAR(120) NOT NULL,
                phone VARCHAR(20) NOT NULL UNIQUE,
                email VARCHAR(255),
                password_hash VARCHAR(255) NOT NULL,
                role VARCHAR(20) NOT NULL,
                language VARCHAR(10) NOT NULL,
                location_name VARCHAR(160),
                latitude FLOAT,
                longitude FLOAT,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL
            )"""
        )
        connection.execute(
            "INSERT INTO farmers (id, name, phone, password_hash, role, language, created_at, updated_at) "
            "VALUES (1, 'Existing Farmer', '+919999999999', 'hash', 'farmer', 'en', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"
        )

    environment = os.environ.copy()
    environment["DATABASE_URL"] = f"sqlite:///{database_path.as_posix()}"
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=BACKEND_DIR,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr

    engine = create_engine(environment["DATABASE_URL"])
    try:
        inspector = inspect(engine)
        assert "farms" in inspector.get_table_names()
        assert {
            "audit_logs",
            "chat_conversations",
            "chat_messages",
            "disease_detections",
            "detection_feedback",
            "expert_reviews",
            "fertilizer_recommendations",
            "notifications",
            "payments",
            "plans",
            "refresh_tokens",
            "soil_tests",
            "subscriptions",
        }.issubset(inspector.get_table_names())
        assert {"state", "district"}.issubset(
            {column["name"] for column in inspector.get_columns("farmers")}
        )
        with engine.connect() as connection:
            assert connection.exec_driver_sql("SELECT name FROM farmers WHERE id = 1").scalar_one() == "Existing Farmer"
    finally:
        engine.dispose()
