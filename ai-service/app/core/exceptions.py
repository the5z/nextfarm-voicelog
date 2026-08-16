from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.utils.logger import logger


def get_request_id(request: Request) -> str:
    return getattr(
        request.state,
        "request_id",
        "unknown",
    )


def register_exception_handlers(app: FastAPI) -> None:
    """
    Register global exception handlers for the FastAPI application.
    """

    @app.exception_handler(HTTPException)
    async def http_exception_handler(
        request: Request,
        exc: HTTPException,
    ) -> JSONResponse:
        request_id = get_request_id(request)

        logger.warning(
            "HTTP exception | request_id=%s | method=%s | path=%s | "
            "status_code=%s | detail=%s",
            request_id,
            request.method,
            request.url.path,
            exc.status_code,
            exc.detail,
        )

        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "message": str(exc.detail),
                "data": None,
                "request_id": request_id,
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        request_id = get_request_id(request)

        logger.warning(
            "Request validation failed | request_id=%s | "
            "method=%s | path=%s | errors=%s",
            request_id,
            request.method,
            request.url.path,
            exc.errors(),
        )

        return JSONResponse(
            status_code=422,
            content={
                "success": False,
                "message": "Request validation failed.",
                "data": {
                    "errors": exc.errors(),
                },
                "request_id": request_id,
            },
        )

    @app.exception_handler(Exception)
    async def unexpected_exception_handler(
        request: Request,
        exc: Exception,
    ) -> JSONResponse:
        request_id = get_request_id(request)

        logger.exception(
            "Unexpected server error | request_id=%s | "
            "method=%s | path=%s",
            request_id,
            request.method,
            request.url.path,
        )

        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": "Internal server error.",
                "data": None,
                "request_id": request_id,
            },
        )