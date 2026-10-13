from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.rate_limit import public_lookup_limiter
from app.modules.service_status.application.use_cases import lookup_public_status
from app.modules.service_status.api.schemas import PublicLookupRequest, PublicServiceStatusResponse
from app.modules.service_status.infrastructure.repository import SqlAlchemyPublicServiceRepository

router = APIRouter(prefix="/api/public", tags=["HU-07 - Estado público"])
SessionDependency = Session


@router.post("/service-status", response_model=PublicServiceStatusResponse)
def public_service_status(
    request: PublicLookupRequest,
    session: Session = Depends(get_db),
    response: Response = None,
) -> PublicServiceStatusResponse:
    client_key = request.tracking_code.strip().upper()
    if not public_lookup_limiter.allow(client_key):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Demasiadas solicitudes. Intente más tarde.",
        )
    repository = SqlAlchemyPublicServiceRepository(session)
    result = lookup_public_status(repository, request.tracking_code)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No existe información pública para ese código.",
        )
    if response is not None:
        response.headers["Cache-Control"] = "no-store"
    return PublicServiceStatusResponse.model_validate(result)
