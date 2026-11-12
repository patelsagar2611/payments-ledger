from collections.abc import Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from testcontainers.community.postgres import PostgresContainer

ALEMBIC_INI = Path(__file__).parents[1] / "alembic.ini"


@pytest.fixture(scope="session")
def postgres_url() -> Iterator[str]:
    """Start a throwaway Postgres container, migrate it to head, yield its URL.

    Started once per test run and removed afterwards. Tests are isolated by
    data (every test creates accounts with fresh ids), so nothing is cleaned
    between tests.
    """
    with PostgresContainer("postgres:17", driver="asyncpg") as container:
        url = container.get_connection_url()

        config = Config(ALEMBIC_INI)
        config.set_main_option("sqlalchemy.url", url)
        command.upgrade(config, "head")

        yield url
