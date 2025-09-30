from fastapi import APIRouter

from app.api.v1.endpoints import applications, auth, users, hotels, program_hotels

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["Авторизация"])
api_router.include_router(applications.router, prefix="/applications", tags=["Заявки"])
api_router.include_router(users.router, prefix="/users", tags=["Личный кабинет"])
api_router.include_router(hotels.router, prefix="/hotels", tags=["Отели"])
api_router.include_router(program_hotels.router, prefix="/program-hotels", tags=["Отели программы"])