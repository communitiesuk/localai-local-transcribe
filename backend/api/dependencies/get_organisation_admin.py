from typing import Annotated

from fastapi import Depends, HTTPException

from backend.api.dependencies.get_current_user import UserDep
from backend.api.dependencies.get_organisation import OrganisationDep
from common.auth import is_admin_for_org
from common.database.postgres_models import Organisation


async def get_org_admin(
    user: UserDep,
    organisation: OrganisationDep,
) -> Organisation:
    if not is_admin_for_org(user, organisation):
        raise HTTPException(
            status_code=403,
            detail="Only an organisation admin can perform this action",
        )

    return organisation


OrganisationAdminDep = Annotated[Organisation, Depends(get_org_admin)]
