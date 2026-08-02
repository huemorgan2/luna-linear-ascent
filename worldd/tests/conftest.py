from __future__ import annotations

import os

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

TEST_DB = os.environ.get(
    "ASCENT_TEST_DATABASE_URL",
    "postgresql://ascent:ascent@localhost:5434/ascent_world")

os.environ.setdefault("DATABASE_URL", TEST_DB)
os.environ.setdefault("ASCENT_SHARED_SECRET", "test-shared-secret")
os.environ.setdefault("ASCENT_ADMIN_KEY", "test-admin-key")
# tests hammer a single tenant; don't trip the production rate limits
os.environ.setdefault("ASCENT_RATE_CAPACITY", "100000")
os.environ.setdefault("ASCENT_ENROLL_PER_HOUR", "100000")
os.environ.setdefault("ASCENT_SIGNUP_PER_HOUR", "100000")


@pytest_asyncio.fixture
async def client():
    from app.config import reset_config
    reset_config()
    from app.main import app

    async with app.router.lifespan_context(app):
        # 004: a name is unique in a world, and this test database is one
        # world that every run walks back into. The suite founds Stew and
        # Fleet over and over — in a real world that is a stranger taking
        # your name; here it is the same fixture on its second call. Climber
        # reservations are cleared per test; that names are unique at all is
        # proven inside tests/test_names.py, within one test.
        from app import db as _db
        if _db.ready():
            await (await _db.get_pool()).execute(
                "DELETE FROM ascent_names WHERE kind = 'climber'")
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            yield c


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"
