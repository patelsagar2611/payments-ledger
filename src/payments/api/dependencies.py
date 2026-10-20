from typing import Annotated

from fastapi import Depends, Request

from payments.ledger.ledger_repository import LedgerRepository


def get_repository(request: Request) -> LedgerRepository:
    """Return the repository the app was created with."""
    repository: LedgerRepository = request.app.state.repository
    return repository


RepositoryDep = Annotated[LedgerRepository, Depends(get_repository)]
