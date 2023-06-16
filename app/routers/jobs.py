from fastapi import APIRouter, Path, HTTPException, status
from math import ceil
from typing import Annotated
from app.models.schemas import PageRequest, JobsPage, JobSchema, PaginationMeta
from app.models.dbmodel import Job

router = APIRouter()


@router.post("/page")
async def get_jobs(page: PageRequest) -> JobsPage:
    jobs_count = Job.select(Job.expired == False).count()
    pages_count = ceil(jobs_count / page.per_page)
    if page.page <= pages_count:
        jobs: list[JobSchema] = []
        for job in (
            Job.select()
            .where(Job.expired == False)
            .order_by(-Job.created_on)
            .paginate(page.page, page.per_page)
        ):
            jobs.append(job.to_schema(JobSchema))
        return JobsPage(
            meta=PaginationMeta(
                total_count=jobs_count,
                current_page=page.page,
                page_count=pages_count,
                per_page=page.per_page,
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
