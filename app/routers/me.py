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
    PersonalitySchema,
)
from app.models.dbmodel import Seeker, Employer, User, Role
from peewee import IntegrityError
from app.deps import get_current_user, Scopes
from typing import Annotated


router = APIRouter()


@router.get("/")
async def get_me(
    current_user: Annotated[User, Security(get_current_user, scopes=Scopes.me)]
) -> UserSchema:
    return current_user.to_schema(UserSchema)


@router.delete("/")
async def logout(current_user: Annotated[User, Security(get_current_user)]):
    current_user.logged_in = False
    current_user.save()


@router.get("/personlities")
async def get_personlities(
    current_user: Annotated[
        User, Security(get_current_user, scopes=Scopes.me + Scopes.seeker)
    ]
) -> list[PersonalitySchema]:
    return list(
        map(lambda x: x.to_schema(PersonalitySchema), current_user.seeker.select())
    )
