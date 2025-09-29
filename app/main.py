from fastapi import FastAPI

from app.api.v1.router import api_router
from app.core.config import settings
from app.db.base import Base
from app.db.session import engine

app = FastAPI(
    title=settings.project_name,
    description="API островка жи есть",
    version="1.0.0",
    contact={
        "name": "Разрабы",
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


@app.get(
    "/health",
    tags=["Служебные"],
    summary="Проверка состояния",
    description="Думаю тут описания излишни",
)
def healthcheck():
    return {"status": "ok"}
