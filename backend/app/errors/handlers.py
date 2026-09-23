import logging

from fastapi import (
    FastAPI,
    HTTPException,
    Request,
)

from fastapi.exceptions import (
    RequestValidationError,
)

from fastapi.responses import (
    JSONResponse,
)


logger = logging.getLogger(
    "uvicorn.error"
)


def register_exception_handlers(
    app: FastAPI,
):
    """
    Register consistent JSON error responses
    for the whole SupplyChain Copilot API.
    """

    # ==============================================
    # FastAPI HTTP errors
    # ==============================================

    @app.exception_handler(
        HTTPException
    )
    async def http_exception_handler(
        request: Request,
        exc: HTTPException,
    ):
        message = (
            exc.detail
            if isinstance(
                exc.detail,
                str,
            )
            else "Request failed."
        )

        return JSONResponse(
            status_code=exc.status_code,
            content={
                "status": "error",
                "error_type":
                    "HTTPException",
                "message": message,
                "details":
                    exc.detail,
                "path":
                    request.url.path,
            },
        )


    # ==============================================
    # Validation errors
    # ==============================================

    @app.exception_handler(
        RequestValidationError
    )
    async def validation_exception_handler(
        request: Request,
        exc: RequestValidationError,
    ):
        return JSONResponse(
            status_code=422,
            content={
                "status": "error",
                "error_type":
                    "ValidationError",
                "message":
                    "Invalid request data.",
                "details":
                    exc.errors(),
                "path":
                    request.url.path,
            },
        )


    # ==============================================
    # Unexpected server errors
    # ==============================================

    @app.exception_handler(
        Exception
    )
    async def general_exception_handler(
        request: Request,
        exc: Exception,
    ):
        logger.exception(
            "Unhandled error on %s",
            request.url.path,
        )

        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "error_type":
                    type(exc).__name__,
                "message":
                    "An internal server error occurred.",
                "path":
                    request.url.path,
            },
        )