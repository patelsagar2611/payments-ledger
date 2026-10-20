from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from payments.domain.errors import ConflictError, DomainError


def register_exception_handlers(app: FastAPI) -> None:
    """Map exception categories to HTTP status codes.

    Starlette picks the handler for the first class in the exception's MRO
    that has one registered, so each error must belong to one category only.
    """

    @app.exception_handler(LookupError)
    async def handle_not_found(request: Request, exc: LookupError) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(ConflictError)
    async def refused_as_of_current_state(
        request: Request, exc: ConflictError
    ) -> JSONResponse:
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    @app.exception_handler(DomainError)
    async def request_not_acceptable(
        request: Request, exc: DomainError
    ) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": str(exc)})
