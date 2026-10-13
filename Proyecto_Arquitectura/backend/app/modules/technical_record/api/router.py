from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.core.security import create_access_token, verify_password
from app.modules.technical_record.api.dependencies import require_staff
from app.modules.technical_record.api.schemas import (
    LoginRequest,
    ObservationCreate,
    ObservationResponse,
    TechnicalRecordResponse,
    TechnicalSpecificationsUpdate,
    TokenResponse,
)
from app.modules.technical_record.application.use_cases import (
    add_technical_observation,
    find_technical_record,
    update_technical_specifications,
)
from app.modules.technical_record.domain.entities import (
    BatterySpecification,
    ControllerConfiguration,
    normalize_serial_number,
)
from app.modules.technical_record.infrastructure.models import StaffUser
from app.modules.technical_record.infrastructure.repository import (
    SqlAlchemyTechnicalRecordRepository,
)

router = APIRouter(prefix="/api/v1", tags=["HU-06 - Expediente técnico"])
SessionDependency = Annotated[Session, Depends(get_db)]
StaffDependency = Annotated[StaffUser, Depends(require_staff)]


@router.post("/auth/token", response_model=TokenResponse)
def login(
    request: LoginRequest, session: SessionDependency, response: Response
) -> TokenResponse:
    user = session.scalar(
        select(StaffUser).where(StaffUser.username == request.username.strip())
    )
    if (
        user is None
        or not user.is_active
        or not verify_password(request.password, user.password_hash)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token(subject=user.id, role=user.role)
    settings = get_settings()
    response.headers["Cache-Control"] = "no-store"
    return TokenResponse(
        access_token=token,
        expires_in=settings.jwt_expires_minutes * 60,
    )


@router.get(
    "/technical-records/by-serial/{serial_number}",
    response_model=TechnicalRecordResponse,
)
def read_technical_record(
    serial_number: str,
    session: SessionDependency,
    _staff: StaffDependency,
    response: Response,
) -> TechnicalRecordResponse:
    normalized = normalize_serial_number(serial_number)
    if not normalized or len(normalized) > 64:
        raise HTTPException(
            status_code=422,
            detail="La serie/chasis debe tener entre 1 y 64 caracteres.",
        )
    record = find_technical_record(
        SqlAlchemyTechnicalRecordRepository(session), normalized
    )
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehículo no encontrado.",
        )
    response.headers["Cache-Control"] = "no-store"
    return TechnicalRecordResponse.model_validate(record)


@router.post(
    "/technical-records/{vehicle_id}/observations",
    response_model=ObservationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_observation(
    vehicle_id: str,
    request: ObservationCreate,
    session: SessionDependency,
    staff: StaffDependency,
    response: Response,
) -> ObservationResponse:
    try:
        observation = add_technical_observation(
            SqlAlchemyTechnicalRecordRepository(session),
            vehicle_id=vehicle_id,
            author_id=staff.id,
            content=request.content,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error
    if observation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehículo no encontrado.",
        )
    response.headers["Cache-Control"] = "no-store"
    return ObservationResponse.model_validate(observation)


@router.put(
    "/technical-records/{vehicle_id}/specifications",
    response_model=TechnicalRecordResponse,
)
def update_specifications(
    vehicle_id: str,
    request: TechnicalSpecificationsUpdate,
    session: SessionDependency,
    staff: StaffDependency,
    response: Response,
) -> TechnicalRecordResponse:
    battery = (
        BatterySpecification(**request.battery.model_dump())
        if request.battery is not None
        else None
    )
    controller = (
        ControllerConfiguration(**request.controller.model_dump())
        if request.controller is not None
        else None
    )
    record = update_technical_specifications(
        SqlAlchemyTechnicalRecordRepository(session),
        vehicle_id=vehicle_id,
        battery=battery,
        controller=controller,
    )
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehículo no encontrado.",
        )
    response.headers["Cache-Control"] = "no-store"
    return TechnicalRecordResponse.model_validate(record)
