"""JSON API. Field errors use the shared validation result."""

import json
import logging

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from starlette.requests import Request

from app.dependencies import get_service
from app.service import ExpenseService
from app.validation import ValidationFailed

logger = logging.getLogger("expense_portal")
router = APIRouter(prefix="/api")


def error_body(exc: ValidationFailed) -> dict[str, list[dict[str, str]]]:
    return {"errors": [{"field": error.field, "message": error.message} for error in exc.errors]}


@router.post("/expenses")
async def create_expense(request: Request, service: ExpenseService = Depends(get_service)) -> JSONResponse:
    try:
        payload = await request.json()
    except json.JSONDecodeError:
        logger.info("Rejected expense create because the body was not JSON")
        return JSONResponse(
            status_code=422,
            content={"errors": [{"field": "body", "message": "Request body must be a JSON object."}]},
        )
    try:
        expense = service.create(payload)
    except ValidationFailed as exc:
        return JSONResponse(status_code=422, content=error_body(exc))
    return JSONResponse(status_code=201, content=expense.as_dict())


@router.get("/expenses")
def list_expenses(
    category: str | None = None,
    start: str | None = None,
    end: str | None = None,
    service: ExpenseService = Depends(get_service),
) -> JSONResponse:
    try:
        expenses = service.list_expenses(category, start, end)
    except ValidationFailed as exc:
        return JSONResponse(status_code=422, content=error_body(exc))
    return JSONResponse(content={"expenses": [expense.as_dict() for expense in expenses]})


@router.get("/dashboard")
def dashboard(service: ExpenseService = Depends(get_service)) -> dict[str, object]:
    return service.dashboard().as_dict()
