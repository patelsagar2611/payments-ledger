from fastapi import FastAPI

from payments.api import accounts, transfers
from payments.api.errors import register_exception_handlers
from payments.ledger.in_memory_repository import InMemoryLedgerRepository
from payments.ledger.ledger_repository import LedgerRepository


def create_app(repository: LedgerRepository | None = None) -> FastAPI:
    """Build the API around a repository; defaults to an empty in-memory one."""
    app = FastAPI(title="Payments Ledger")
    app.state.repository = (
        repository if repository is not None else InMemoryLedgerRepository()
    )
    register_exception_handlers(app)
    app.include_router(accounts.router)
    app.include_router(transfers.router)
    return app
