from fastapi import APIRouter, Depends, Query, Path, HTTPException, status, Security
from app.deps import get_user_or_none, Scopes
from typing import Annotated, Literal
from app.models.dbmodel import Guide, User, JobCategory, Personality
from app.models.schemas import GuideItem, GuideSchema, Role, GuidesPage, PaginationMeta
from ordered_set import OrderedSet
from peewee import IntegrityError
from pydantic import PositiveInt
from math import ceil

router = APIRouter()


@router.get("/search")
async def search_guides(
    course: Annotated[str, Query()] = None,
    expertise: Annotated[str, Query()] = None,
    min_salary: Annotated[int, Query(ge=1)] = None,
    max_salary: Annotated[int, Query(ge=1)] = None,
    personality: Annotated[str, Query()] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(le=100, ge=1)] = 10,
    user: Annotated[User | None, Depends(get_user_or_none(Scopes.seeker))] = None,
) -> GuidesPage:
    q = JobCategory.slug == JobCategory.slug
    if course:
        q = JobCategory.course == course
        if expertise:
            q &= JobCategory.expertise == expertise

    if min_salary:
        q &= JobCategory.min_salary >= min_salary

    if max_salary:
        q &= JobCategory.max_salary >= max_salary

    if user and personality:
        seeker = user.seeker
        personality = Personality.get_by_id(personality)  # TODO: Error handle
        if personality >> seeker.personalities:
            q &= personality >> JobCategory.personalities

    count = JobCategory.select().where(q).count()
    if count == 0:
        raise HTTPException(status.HTTP_204_NO_CONTENT)
    pages_count = ceil(count / per_page)
    if page <= pages_count:
        guides = []
        for jc in JobCategory.select().where(q).paginate(page, per_page):
            guides.extend([guide.to_schema(GuideItem) for guide in jc.guides])
        return GuidesPage(
            meta=PaginationMeta(
                total_count=count,
                current_page=page,
                page_count=pages_count,
                per_page=per_page,
            ),
            guides=guides,
        )
    else:
        HTTPException(400, "bad_pagination")


@router.get("/")
async def get_guides(
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(le=100, ge=1)] = 10,
) -> GuidesPage:
    count = Guide.select().count()
    if count == 0:
        raise HTTPException(status.HTTP_204_NO_CONTENT)
    pages_count = ceil(count / per_page)
    if page <= pages_count:
        return GuidesPage(
            meta=PaginationMeta(
                total_count=count,
                current_page=page,
                page_count=pages_count,
                per_page=per_page,
            ),
            guides=[
                guide.to_schema(GuideItem)
                for guide in Guide.select().paginate(page, per_page)
            ],
        )
    else:
        HTTPException(400, "bad_pagination")


@router.get("/{slug}")
async def get_guide(slug: Annotated[str, Path()]) -> GuideSchema:
    try:
        if slug:
            return Guide.get(Guide.slug == slug).to_schema(GuideSchema)
        raise HTTPException(status.HTTP_400_BAD_REQUEST)
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="guide.not_found"
        )
