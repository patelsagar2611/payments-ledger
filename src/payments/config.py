"""Settings read from the environment.

The database location arrives as separate variables rather than one URL, so a
password managed by a secrets store can be injected on its own without being
pasted into a connection string.
"""

import os

from sqlalchemy import URL

DRIVER = "postgresql+asyncpg"
DEFAULT_PORT = 5432
REQUIRED_VARS = ("DB_HOST", "DB_NAME", "DB_USER", "DB_PASSWORD")


def database_url() -> URL:
    """Build the Postgres URL from DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD.

    DB_PORT is optional (5432). Every other variable is required: refuse to
    start, naming all missing ones, rather than connect somewhere unintended.
    The password is passed raw; URL.create escapes characters such as @ / :
    that would otherwise be read as URL separators.
    """
    missing = [name for name in REQUIRED_VARS if not os.environ.get(name)]
    if missing:
        raise RuntimeError(f"missing {', '.join(missing)}; refusing to start.")

    port = os.environ.get("DB_PORT") or str(DEFAULT_PORT)
    return URL.create(
        DRIVER,
        username=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        host=os.environ["DB_HOST"],
        port=int(port),
        database=os.environ["DB_NAME"],
    )
