from fastapi import APIRouter, Depends, Query, Path, HTTPException, status
from app.deps import get_user_or_none
from typing import Annotated, Literal
from app.models.dbmodel import Seeker, Guide
from app.models.schemas import GuideItem, GuideSchema
from ordered_set import OrderedSet
from peewee import IntegrityError

router = APIRouter()


@router.get("/search1")
async def search1(
    branch: Annotated[str | None, Query()] = None,
    expertise: Annotated[str | None, Query()] = None,
    user: Annotated[Seeker | None, Depends(get_user_or_none("seeker"))] = None,
    filter: Annotated[None | Literal["personal"], Query()] = None,
) -> OrderedSet[GuideItem]:
    result = OrderedSet()
    query = None
    if branch:
        query = Guide.branch == branch
    if branch and expertise:
        query &= Guide.expertise == expertise
    if user:
        for personality in user.personalities:
            for guide in personality.guides.where(query):
                guide.based_on_personality = True
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
) -> OrderedSet[GuideItem]:
    raise NotImplementedError  # TODO


@router.get("/{slug}")
async def get_guide(slug: Annotated[str, Path()]) -> GuideSchema:
    try:
        return Guide.get(Guide.slug == slug).to_schema(GuideSchema)
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="guide.not_found"
        )
