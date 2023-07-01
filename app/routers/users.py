from fastapi import APIRouter, HTTPException, status, Security, Path
from fastapi_utils.inferring_router import InferringRouter
from fastapi_utils.cbv import cbv
from app.models.schemas import EmployerSchema
from app.models.dbmodel import Seeker, Employer, User, Role
from peewee import DoesNotExist
from app.deps import get_current_user, Scopes
from typing import Annotated

router = APIRouter()


@router.get("/employer/{id}")
async def get_user_info(id: Annotated[str, Path]) -> EmployerSchema:
    try:
        user = User.get_by_id(id)
        if user.role == Role.employer and user.visible and not user.disabled:
            return user.employer.to_schema(EmployerSchema)
    except DoesNotExist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="user.notfound"
        )
