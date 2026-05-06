from contextlib import asynccontextmanager

from exception_handlers import (
    global_exception_handler,
    http_exception_handler,
    validation_exception_handler,
)
from fastapi.exceptions import RequestValidationError
from fastapi.responses import PlainTextResponse
from middlewares.request_context import request_context_middleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from fastapi import FastAPI
from routers import (
    alerts,
    dt,
    feedback,
    indicators,
    links,
    pauses,
    screenshots,
    subscriptions,
    users,
)
from routers import rules as group_rules


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Управление жизненным циклом приложения.
    Выделенный lifecycle-хук оставлен для будущих startup/shutdown задач.
    """
    yield


app = FastAPI(
    openapi_url="/alerts/openapi.json",
    docs_url="/alerts/docs",
    redoc_url="/alerts/redoc",
    title="Alerts service API",
    lifespan=lifespan,
)

app.middleware("http")(request_context_middleware)


@app.get(
    "/alerts/health",
    tags=["health"],
    summary="Проверка работоспособности сервиса",
    description="Возвращает OK, если сервис работает.",
)
async def api_health() -> PlainTextResponse:
    return PlainTextResponse("OK", status_code=200)


app.include_router(alerts.router)
app.include_router(alerts.duplicate_router)
app.include_router(indicators.router)
app.include_router(links.router)
app.include_router(group_rules.router)
app.include_router(subscriptions.router)
app.include_router(users.router)
app.include_router(feedback.router)
app.include_router(dt.router)
app.include_router(pauses.router)
app.include_router(screenshots.router)


app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8888)
