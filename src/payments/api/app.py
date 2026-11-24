from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from payments.api import accounts, health, transfers
from payments.api.errors import register_exception_handlers
from payments.config import database_url
from payments.ledger.ledger_repository import LedgerRepository
from payments.ledger.postgres_repository import PostgresLedgerRepository


def create_app(repository: LedgerRepository | None = None) -> FastAPI:
    """Build the API around a repository.

    With no repository given, connect to the Postgres described by the DB_*
    environment variables. database_url() refuses to start if any are missing:
    a ledger must never silently run without a database.
    """
    engine: AsyncEngine | None = None
    if repository is None:
        engine = create_async_engine(database_url())
        repository = PostgresLedgerRepository(engine)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        yield
        # Close only an engine this function created; a repository passed in
        # belongs to the caller, who disposes of it.
        if engine is not None:
            await engine.dispose()

    app = FastAPI(title="Payments Ledger", lifespan=lifespan)
    app.state.repository = repository
    register_exception_handlers(app)
    app.include_router(accounts.router)
    app.include_router(transfers.router)
    app.include_router(health.router)
    return app
