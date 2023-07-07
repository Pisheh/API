from fastapi import APIRouter, Security
from app.models.schemas import (
    MyInfoSchema,
    PersonalitySchema,
)
from app.models.dbmodel import User
from app.deps import get_current_user, Scopes
from typing import Annotated


router = APIRouter()


@router.get("/")
async def get_me(
    current_user: Annotated[User, Security(get_current_user, scopes=Scopes.me)]
) -> MyInfoSchema:
    return current_user.to_schema(MyInfoSchema)


@router.get("/personlities")
async def get_personlities(
    current_user: Annotated[
        User, Security(get_current_user, scopes=Scopes.me + Scopes.seeker)
    ]
) -> list[PersonalitySchema]:
    return list(
        map(lambda x: x.to_schema(PersonalitySchema), current_user.seeker.select())
    )
