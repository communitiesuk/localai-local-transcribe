import logging
import uuid

from fastapi import APIRouter, HTTPException
from sqlmodel import select

from backend.api.dependencies import OrganisationAdminDep, SQLSessionDep, UserDep
from common.auth import is_system_admin
from common.database.postgres_models import Organisation
from common.types import OrganisationCreateRequest, OrganisationPatchRequest, OrganisationResponse

logger = logging.getLogger(__name__)
organisations_router = APIRouter(tags=["Organisations"])


@organisations_router.get("/organisations", response_model=list[OrganisationResponse], status_code=200)
async def list_organisations(
    session: SQLSessionDep,
    user: UserDep,
) -> list[OrganisationResponse]:
    """List all organisations. Only accessible to system admins.."""
    if not is_system_admin(user):
        raise HTTPException(status_code=403, detail="Not authorized to access this resource")

    result = await session.exec(select(Organisation).order_by(Organisation.name))
    return [OrganisationResponse.model_validate(org) for org in result.all()]


@organisations_router.get("/organisations/{organisation_id}", response_model=OrganisationResponse, status_code=200)
async def get_organisation(organistaion: OrganisationAdminDep) -> OrganisationResponse:
    """Get organisation. Only accessible to organisation admins."""
    return OrganisationResponse.model_validate(organistaion)


@organisations_router.post("/organisations", response_model=OrganisationResponse, status_code=201)
async def create_organisation(
    request: OrganisationCreateRequest,
    session: SQLSessionDep,
    user: UserDep,
) -> OrganisationResponse:
    """Create a new organisation. Only accessible to system admins."""
    if not is_system_admin(user):
        raise HTTPException(status_code=403, detail="Not authorized to access this resource")

    result = await session.exec(select(Organisation).where(Organisation.name == request.name))
    existing_org = result.first()
    if existing_org:
        raise HTTPException(status_code=409, detail="Organisation with this name already exists")

    new_org = Organisation(
        name=request.name,
        allowed_domains=request.allowed_domains,
    )
    session.add(new_org)
    await session.commit()
    await session.refresh(new_org)
    logger.info("Created new organisation with id %s and name %s", new_org.id, new_org.name)
    return OrganisationResponse.model_validate(new_org)


@organisations_router.delete("/organisations/{organisation_id}", status_code=204)
async def delete_organisation(
    organisation_id: uuid.UUID,
    session: SQLSessionDep,
    user: UserDep,
) -> None:
    """Delete an organisation. Only accessible to system admins."""
    if not is_system_admin(user):
        raise HTTPException(status_code=403, detail="Not authorized to access this resource")

    org = await session.get(Organisation, organisation_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organisation not found")

    await session.delete(org)
    await session.commit()


@organisations_router.patch("/organisations/{organisation_id}", response_model=OrganisationResponse, status_code=200)
async def update_organisation(
    organisation_id: uuid.UUID,
    request: OrganisationPatchRequest,
    session: SQLSessionDep,
    user: UserDep,
) -> OrganisationResponse:
    """Update an organisation's allowed email domains. Only accessible to system admins."""
    if not is_system_admin(user):
        raise HTTPException(status_code=403, detail="Not authorized to access this resource")

    org = await session.get(Organisation, organisation_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organisation not found")

    org.allowed_domains = request.allowed_domains
    await session.commit()
    await session.refresh(org)
    logger.info(
        "Updated allowed domains for organisation %s. Count=%s",
        org.id,
        len(org.allowed_domains),
    )
    return OrganisationResponse.model_validate(org)
