from backend.api.dependencies import get_organisation_admin
from backend.api.dependencies import get_organisation_admin
from backend.api.dependencies import get_organisation_admin
import logging
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, Query
from sqlmodel import select

from backend.api.dependencies import SQLSessionDep, UserDep
from backend.utils.constants import DEFAULT_PAGE, DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from backend.utils.queries import get_paginated_users
from common.auth import is_admin_for_org, is_system_admin
from common.database.postgres_models import Organisation
from common.types import (
    OrganisationCreateRequest,
    OrganisationPatchRequest,
    OrganisationResponse,
    PaginatedUsersResponse,
)

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
async def get_organisation(user: UserDep, session: SQLSessionDep, organisation_id: uuid.UUID) -> OrganisationResponse:
    """Get organisation. Only accessible to organisation admins."""
    organisation = await session.get(Organisation, organisation_id)
    if organisation is None:
        raise HTTPException(status_code=404, detail="Organisation not found")

    if not is_admin_for_org(user, organisation):
        raise HTTPException(status_code=403, detail="Not authorized to access this resource")

    return OrganisationResponse.model_validate(organisation)


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
    """Update an organisation's allowed email domains. Accessible to system admins or the organisation's own admin."""
    org = await session.get(Organisation, organisation_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organisation not found")

    if not is_admin_for_org(user, org):
        raise HTTPException(status_code=403, detail="Not authorized to access this resource")

    if org.updated_datetime != request.updated_datetime:
        raise HTTPException(
            status_code=409,
            detail="This organisation was updated by someone else. Please reload and try again.",
        )

    org.allowed_domains = request.allowed_domains
    org.updated_datetime = datetime.now(tz=UTC)
    await session.commit()
    await session.refresh(org)
    logger.info(
        "Updated allowed domains for organisation %s. Count=%s",
        org.id,
        len(org.allowed_domains),
    )
    return OrganisationResponse.model_validate(org)


@organisations_router.get(
    "/organisations/{organisation_id}/users",
    response_model=PaginatedUsersResponse,
    status_code=200,
)
async def list_organisations_users(
    organisation_id: uuid.UUID,
    session: SQLSessionDep,
    user: UserDep,
    page: int = Query(DEFAULT_PAGE, ge=DEFAULT_PAGE),
    page_size: int = Query(DEFAULT_PAGE_SIZE, le=MAX_PAGE_SIZE),
) -> PaginatedUsersResponse:
    if not is_system_admin(user):
        raise HTTPException(status_code=403, detail="Not authorized to access this resource")

    organisation = await session.get(Organisation, organisation_id)
    if organisation is None:
        raise HTTPException(status_code=404, detail="Organisation not found")

    return await get_paginated_users(session, organisation, page, page_size)
