"""Give tests an isolated SQLite database initialized through Alembic."""
import atexit
import os
import tempfile
from pathlib import Path

from alembic import command
from alembic.config import Config
import pytest

BACKEND_DIR = Path(__file__).resolve().parents[1]
TEST_DATABASE = tempfile.NamedTemporaryFile(prefix="farmwise-test-", suffix=".sqlite", delete=False)
TEST_DATABASE.close()
atexit.register(lambda: Path(TEST_DATABASE.name).unlink(missing_ok=True))

os.environ["APP_ENV"] = "test"
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DATABASE.name.replace(os.sep, '/')}"

alembic_config = Config(str(BACKEND_DIR / "alembic.ini"))
alembic_config.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
command.upgrade(alembic_config, "head")


@pytest.fixture(autouse=True)
def isolate_rate_limit_state():
    from app.core.limiter import limiter

    limiter.reset()
    yield
    limiter.reset()


def cleanup_test_database() -> None:
    try:
        from app.core.database import engine

        engine.dispose()
    except (ImportError, RuntimeError):
        pass
    try:
        Path(TEST_DATABASE.name).unlink(missing_ok=True)
    except PermissionError:
        # Windows may keep a SQLite handle open until interpreter shutdown.
        pass


atexit.register(cleanup_test_database)
