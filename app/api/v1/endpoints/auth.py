from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db_session
from app.core.security import create_access_token
from app.models.user import User
from app.schemas.auth import Token
from app.schemas.user import UserCreate, UserRead
from app.services import auth_service

router = APIRouter()


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Регистрация кандидата",
    description="Создаёт нового участника программы. Email должен быть уникальным, пароль будет зашифрован.",
)
def register_user(user_in: UserCreate, db: Session = Depends(get_db_session)):
    print("register print")
    existing_user = auth_service.get_user_by_email(db, email=user_in.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email уже зарегистрирован")

    user = auth_service.create_user(
        db,
        email=user_in.email,
        password=user_in.password,
        first_name=user_in.first_name,
        last_name=user_in.last_name,
    )
    return user


@router.post(
    "/login",
    response_model=Token,
    summary="Получение токена",
    description=(
        "Возвращает JWT токен по email и паролю. Вставьте его в форму авторизации Swagger как `Bearer <токен>`"
    ),
)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db_session),
) -> Token:
    user = auth_service.authenticate_user(db, email=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Неверный email или пароль")

    access_token = create_access_token(subject=user.id)
    return Token(access_token=access_token)


@router.get(
    "/me",
    response_model=UserRead,
    summary="Профиль текущего пользователя",
    description="Возвращает информацию о пользователе, чей токен передан в запросе.",
)
def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user
