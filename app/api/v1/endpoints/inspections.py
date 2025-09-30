from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db_session
from app.models.inspection import InspectionStatus
from app.models.user import User
from app.schemas.inspection import InspectionRead, InspectionSelectRequest
from app.services import inspection_service

router = APIRouter()


@router.get(
    "/",
    response_model=list[InspectionRead],
    summary="Список проверок",
    description=(
        "Возвращает список проверок. Пользователь получает только свои проверки, "
        "администратор — все проверки."
    ),
)
def list_inspections(
    db: Session = Depends(get_db_session),
    status_filter: InspectionStatus | None = Query(
        default=None,
        description="Фильтр по статусу проверки",
    ),
    current_user: User = Depends(get_current_active_user),
):
    guest_id = None if current_user.role == "admin" else current_user.id
    return inspection_service.list_inspections(
        db,
        guest_id=guest_id,
        status=status_filter,
    )


@router.get(
    "/{inspection_id}",
    response_model=InspectionRead,
    summary="Детали проверки",
    description="Возвращает подробную информацию о проверке.",
)
def get_inspection(
    inspection_id: int,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
):
    inspection = inspection_service.get_inspection(db, inspection_id)
    if inspection is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Проверка не найдена")

    if current_user.role != "admin" and inspection.guest_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав")

    return inspection


@router.post(
    "/select",
    response_model=InspectionRead,
    status_code=status.HTTP_201_CREATED,
    summary="Выбор отеля для проверки",
    description="Создает новую проверку для текущего пользователя по выбранному отелю.",
)
def select_hotel_for_inspection(
    payload: InspectionSelectRequest,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
):
    try:
        inspection = inspection_service.select_hotel_for_inspection(
            db,
            hotel_id=payload.hotel_id,
            guest_id=current_user.id,
            home_city=payload.home_city,
            preferred_city=payload.preferred_city,
            guests_count=payload.guests_count,
        )
    except inspection_service.InspectionSelectionError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return inspection