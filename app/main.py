from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.v1.router import api_router
from app.core.config import settings
from app.db.base import Base
from app.db.session import engine

app = FastAPI(
    title=settings.project_name,
    description="О!Хакатон 2024. Проект Ostrovok. Backend часть.",
    version="1.0.5",
    contact={
        "name": "Разработчики",
        "email": "support@example.com",
    },
    license_info={
        "name": "MIT",
    },
    swagger_ui_parameters={
        "docExpansion": "none",
        "defaultModelsExpandDepth": -1,
    },
)

Base.metadata.create_all(bind=engine)

app.include_router(api_router, prefix=settings.api_v1_prefix)

static_dir = Path(settings.static_root)
static_dir.mkdir(parents=True, exist_ok=True)
app.mount(settings.static_url, StaticFiles(directory=static_dir, check_dir=False), name="static")

@app.get(
    "/health",
    tags=["Служебные"],
    summary="Проверка состояния",
    description="Проверка состояния сервиса",
)
def healthcheck():
    return {"status": "ok"}
