"""Application entry point."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.database import init_db
from app.routers import api, web
from app.templating import APP_DIR, templates

logger = logging.getLogger("expense_portal")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    logging.basicConfig(level=logging.INFO)
    init_db()
    yield


app = FastAPI(title="Smart Expense Management Portal", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=str(APP_DIR / "static")), name="static")
app.include_router(web.router)
app.include_router(api.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.exception_handler(Exception)
async def unhandled_error(request: Request, exc: Exception):
    # Log the real failure on the server. Callers only see a generic message.
    logger.exception("Unhandled error on %s", request.url.path)
    if request.url.path.startswith("/api") or request.url.path == "/health":
        return JSONResponse(
            status_code=500,
            content={"message": "Something went wrong. Try again."},
        )
    return templates.TemplateResponse(
        request,
        "error.html",
        {"message": "Something went wrong. Try again.", "active": ""},
        status_code=500,
    )
