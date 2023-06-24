from fastapi import APIRouter, Query, Depends, Path, HTTPException
from typing import Annotated, Any, Literal
from app.models.dbmodel import User, JobCategory, Job, TABLES, Personality, Seeker
from app.models.schemas import (
    JobsPage,
    JobSchema,
    PaginationMeta,
    CategoryPage,
    JobCategoryInfo,
)
from app.deps import get_user_or_none, Scopes
from math import ceil
from peewee import DoesNotExist

router = APIRouter()


@router.get("/search")
async def get_categories(
    course: Annotated[str, Query()] = None,
    expertise: Annotated[str, Query()] = None,
    min_salary: Annotated[int, Query(ge=1)] = None,
    max_salary: Annotated[int, Query(ge=1)] = None,
    personality: Annotated[str, Query()] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(le=100, ge=1)] = 10,
    user: Annotated[User | None, Depends(get_user_or_none(Scopes.seeker))] = None,
) -> Any:
    q = JobCategory.slug == JobCategory.slug
    if course:
        q = JobCategory.discipline == course
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


@router.get("/{slug}/jobs")
async def get_category_jobs(
    slug: Annotated[str, Path()],
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(le=100, ge=1)] = 10,
) -> JobsPage:
    try:
        category = JobCategory.get_by_id(slug)
        jobs_count = category.jobs.select(Job.expired == False).count()
        pages_count = ceil(jobs_count / per_page)
        if page <= pages_count:
            jobs: list[JobSchema] = []
            for job in (
                Job.select()
                .where(Job.expired == False)
                .order_by(-Job.created_on)
                .paginate(page, per_page)
            ):
                jobs.append(job.to_schema(JobSchema))
            return JobsPage(
                meta=PaginationMeta(
                    total_count=jobs_count,
                    current_page=page,
                    page_count=pages_count,
                    per_page=per_page,
                ),
                jobs=jobs,
            )
        else:
            HTTPException(400, "jobs.bad_pagination")
    except DoesNotExist:
        HTTPException(404)
