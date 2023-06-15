from fastapi import APIRouter, Depends, Query, Path, HTTPException, status, Security
from app.deps import get_user_or_none, Scopes
from typing import Annotated, Literal
from app.models.dbmodel import Guide, User
from app.models.schemas import GuideItem, GuideSchema
from ordered_set import OrderedSet
from peewee import IntegrityError

router = APIRouter()


@router.get("/search1")
async def search1(
    branch: Annotated[str | None, Query()] = None,
    expertise: Annotated[str | None, Query()] = None,
    user: Annotated[
        User | None, Security(get_user_or_none, scopes=Scopes.me + Scopes.seeker)
    ] = None,
    filter: Annotated[None | Literal["personal"], Query()] = None,
) -> list[GuideItem]:
    seeker = User.seeker
    result = OrderedSet()
    query = None
    if branch:
        query = Guide.branch == branch
    if branch and expertise:
        query &= Guide.expertise == expertise
    if seeker:
        for personality in seeker.personalities:
            for guide in personality.guides.where(query):
                guide.recommended = True
                result.add(guide.to_schema(GuideItem))

        if filter == "personal":
            return result

    for guide in Guide.select().where(query):
        result.add(guide.to_schema(GuideItem))

    return result


@router.get("/search2")
async def search2(
    min_salary: Annotated[int, Query()],
    max_salary: Annotated[int, Query()],
    branches: Annotated[None | list[str], Query()] = None,
) -> list[GuideItem]:
    raise NotImplementedError  # TODO


@router.get("/{slug}")
async def get_guide(slug: Annotated[str, Path()]) -> GuideSchema:
    try:
        return Guide.get(Guide.slug == slug).to_schema(GuideSchema)
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="guide.not_found"
        )
