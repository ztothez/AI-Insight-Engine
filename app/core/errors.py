from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Function logic: return one consistent response for invalid API fields.
    return JSONResponse(
        status_code=422,
        content={
            "error": True,
            "message": "Invalid input. Please provide a valid code snippet, language, and strictness level.",
            "status_code": 422
        }
    )

async def http_exception_handler(request: Request, exc):
    # Function logic: preserve intentional API status codes and messages.
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.detail,
            "status_code": exc.status_code
        }
    )

async def unhandled_exception_handler(request: Request, exc: Exception):
    # Function logic: hide unexpected internal failures behind a safe response.
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "message": "Analysis failed. Please try again.",
            "status_code": 500
        }
    )
