from fastapi import APIRouter, HTTPException, status, Security
from fastapi_utils.inferring_router import InferringRouter
from fastapi_utils.cbv import cbv
from app.models.schemas import (
    UserQuery,
    UserQueryResult,
    UserSchema,
    LoginInfo,
    LoginResult,
    SignupInfo,
)
from app.models.dbmodel import Seeker, Employer, User, Role
from peewee import IntegrityError
from app.deps import get_current_user, Scopes
from typing import Annotated


router = APIRouter()


@router.get("/me")
async def get_me(
    current_user: Annotated[User, Security(get_current_user, scopes=Scopes.me)]
) -> UserSchema:
    return UserSchema(current_user)
