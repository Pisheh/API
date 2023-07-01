from fastapi import APIRouter, Path, HTTPException, status, Query, Depends
from math import ceil
from typing import Annotated
from pydantic import PositiveInt
from app.models.schemas import JobsPage, JobSchema, PaginationMeta
from app.models.dbmodel import Job, User, TABLES
from app.deps import get_user_or_none, Scopes

router = APIRouter()


@router.get("/")
async def get_jobs(
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(le=100, ge=1)] = 10,
) -> JobsPage:
    count = Job.select().where(Job.expired == False).count()
    if count == 0:
        raise HTTPException(status.HTTP_204_NO_CONTENT)
    pages_count = ceil(count / per_page)
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
                total_count=count,
                current_page=page,
                page_count=pages_count,
                per_page=per_page,
            ),
            jobs=jobs,
        )
    else:
        HTTPException(400, "jobs.bad_pagination")


@router.get("/{job_id}")
async def get_jobs(
    job_id: Annotated[int, Path(title="The ID of the job to get", ge=1)]
) -> JobSchema:
    if (job := Job.get_or_none(job_id)) is not None and not job.expired:
        return job.to_schema(JobSchema)
    raise HTTPException(status.HTTP_404_NOT_FOUND, "job.not_found")
