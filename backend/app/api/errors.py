from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.exceptions import ConflictError, DomainError, KeitaroError, NotFoundError, ValidationError


def register_handlers(app: FastAPI) -> None:
    @app.exception_handler(NotFoundError)
    async def _404(request: Request, exc: NotFoundError):
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(ConflictError)
    async def _409(request: Request, exc: ConflictError):
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    @app.exception_handler(ValidationError)
    async def _422(request: Request, exc: ValidationError):
        return JSONResponse(status_code=422, content={"detail": str(exc)})

    @app.exception_handler(KeitaroError)
    async def _502(request: Request, exc: KeitaroError):
        return JSONResponse(status_code=502, content={"detail": str(exc)})

    @app.exception_handler(DomainError)
    async def _domain(request: Request, exc: DomainError):
        return JSONResponse(status_code=400, content={"detail": str(exc)})
