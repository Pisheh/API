from fastapi import APIRouter, Security, Depends, Response, status, HTTPException
from app.models.schemas import MyInfoSchema, PersonalitySchema, UpdateUserInfo, Role
from app.models.dbmodel import User
from app.deps import get_current_user, Scopes, sudo_access
from app.literals import CITIES
from typing import Annotated


router = APIRouter()


@router.get("/")
async def get_me(
    current_user: Annotated[User, Security(get_current_user, scopes=Scopes.me)]
) -> MyInfoSchema:
    return current_user.to_schema(MyInfoSchema)


@router.put(
    "/",
    responses={
        201: {"description": "updated user profile and returned new profile"},
        200: {"description": "user profile didn't changed and returned old profile"},
    },
)
async def update_profile(
    user: Annotated[User, Security(get_current_user, scopes=Scopes.me)],
    sudo_access: Annotated[bool, Depends(sudo_access)],
    data: UpdateUserInfo,
    response: Response,
) -> MyInfoSchema:
    if data.password != data.password_confirm:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="password mismatch")
    user.email = data.email
    user.phone_number = data.phone_number
    user.pass_hash = User.hash_password(data.password)
    s = user.save() == 1
    if user.role == Role.employer:
        employer = user.employer
        employer.co_name = data.employer.co_name
        if data.employer.city in CITIES:
            employer.city = data.employer.city
        s |= employer.save() == 1
    elif user.role == Role.seeker:
        seeker = user.seeker
        seeker.firstname = seeker.firstname
        seeker.lastname = seeker.lastname
        s |= seeker.save() == 1
    if s:
        response.status_code = status.HTTP_201_CREATED
    return user.to_schema(MyInfoSchema)


@router.get("/personlities")
async def get_personlities(
    current_user: Annotated[
        User, Security(get_current_user, scopes=Scopes.me + Scopes.seeker)
    ]
) -> list[PersonalitySchema]:
    return list(
        map(lambda x: x.to_schema(PersonalitySchema), current_user.seeker.select())
    )
