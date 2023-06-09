from fastapi import APIRouter, Depends, Query, Path, HTTPException, status, Security
from app.deps import get_user_or_none, Scopes
from typing import Annotated, Literal
from app.models.dbmodel import Guide, User, JobCategory, Personality, ForeignGuideMeta
from app.models.schemas import (
    GuideItem,
    GuideSchema,
    Role,
    GuidesPage,
    PaginationMeta,
    ForeignGuideMotivation,
    JobType,
    Grade,
)
from ordered_set import OrderedSet
from peewee import IntegrityError
from pydantic import PositiveInt
from math import ceil

router = APIRouter()


def get_guides(query, page, per_page):
    count = JobCategory.select().where(query).count()
    if count == 0:
        raise HTTPException(status.HTTP_204_NO_CONTENT)
    pages_count = ceil(count / per_page)
    if page <= pages_count:
        guides = []
        for jc in JobCategory.select().where(query).paginate(page, per_page):
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


@router.get("/search/1", summary="I know Expertise I love")
async def search1(
    course: Annotated[str, Query()],
    expertise: Annotated[str, Query()] = None,
    personality: Annotated[str, Query()] = None,
    page: Annotated[int, Query(alias="p", ge=1, description="page")] = 1,
    per_page: Annotated[
        int, Query(alias="pp", le=100, ge=1, description="per page")
    ] = 10,
    user: Annotated[User | None, Depends(get_user_or_none(Scopes.seeker))] = None,
) -> GuidesPage:
    q = JobCategory.course == course
    if expertise:
        q &= JobCategory.expertise == expertise

    if user and personality:
        seeker = user.seeker
        try:
            personality = Personality.get_by_id(personality)
            if personality >> seeker.personalities:
                q &= personality >> JobCategory.personalities
        except:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST, detail="invalid personality id"
            )
    return get_guides(q, page, per_page)


@router.get("/search/2", summary="Search to find my Expertise")
async def search2(
    fav: Annotated[list[str], Query(description="User favorite courses")],
    salary: Annotated[
        tuple[int, int], Query(description="minimum and maximum salary")
    ] = None,
    type_: Annotated[JobType, Query(description="Job types", alias="type")] = None,
    personality: Annotated[str, Query()] = None,
    page: Annotated[int, Query(alias="p", ge=1, description="page")] = 1,
    per_page: Annotated[
        int, Query(alias="pp", ge=1, le=50, description="per page")
    ] = 10,
    user: Annotated[User | None, Depends(get_user_or_none(Scopes.seeker))] = None,
) -> GuidesPage:
    query = JobCategory.course >> fav
    if salary:
        query &= (
            JobCategory.min_salary >= salary[0] & JobCategory.max_salary <= salary[1]
        )
    if type_:
        query &= JobCategory.type == type_

    if user and personality:
        seeker = user.seeker
        try:
            personality = Personality.get_by_id(personality)
            if personality >> seeker.personalities:
                query &= personality >> JobCategory.personalities
        except:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST, detail="invalid personality id"
            )

    return get_guides(query, page, per_page)


@router.get("/search/3", summary="Search for guidance in Iran")
async def search3(
    course: Annotated[str, Query()],
    salary: Annotated[tuple[int, int], Query()] = None,
    type_: Annotated[JobType, Query(alias="type")] = None,
    personality: Annotated[str, Query()] = None,
    page: Annotated[int, Query(alias="p", ge=1, description="page")] = 1,
    per_page: Annotated[
        int, Query(alias="pp", ge=1, le=50, description="per page")
    ] = 10,
    user: Annotated[User | None, Depends(get_user_or_none(Scopes.seeker))] = None,
) -> GuidesPage:
    query = JobCategory.course == course
    if salary:
        query &= (
            JobCategory.min_salary >= salary[0] & JobCategory.max_salary <= salary[1]
        )
    if type_:
        query &= JobCategory.type == type_

    if user and personality:
        seeker = user.seeker
        try:
            personality = Personality.get_by_id(personality)
            if personality >> seeker.personalities:
                query &= personality >> JobCategory.personalities
        except:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST, detail="invalid personality id"
            )

    return get_guides(query, page, per_page)


@router.get("/search/4", summary="Search for foreign guidance")
async def search4(
    course: Annotated[str, Query()],
    grade: Annotated[Grade, Query()] = None,
    motivation: Annotated[ForeignGuideMotivation, Query] = None,
    per_page: Annotated[int, Query(ge=1, le=100)] = 10,
    page: Annotated[int, Query(ge=1)] = 1,
) -> GuidesPage:
    q = ForeignGuideMeta.id == ForeignGuideMeta.id
    if course:
        q = ForeignGuideMeta.course == course
    if grade:
        q &= ForeignGuideMeta.grade == grade
    if motivation:
        q &= ForeignGuideMeta.motivation == motivation

    count = ForeignGuideMeta.select().where(q).count()
    if count == 0:
        raise HTTPException(status.HTTP_204_NO_CONTENT)
    pages_count = ceil(count / per_page)
    if page <= pages_count:
        guides = []
        for fgm in ForeignGuideMeta.select().where(q).paginate(page, per_page):
            guides.extend([guide.to_schema(GuideItem) for guide in fgm.guides])
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
