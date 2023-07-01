from fastapi import APIRouter, Path, HTTPException, status, Query, Depends, Security
from math import ceil
from typing import Annotated
from peewee import DoesNotExist
from app.models.schemas import Role, JobRequestSchema, JobRequestPage, PaginationMeta
from app.models.dbmodel import JobRequest, User, Job, TABLES, Employer
from app.deps import get_current_user, Scopes

from datetime import datetime, timedelta

router = APIRouter()


@router.post("/new-request")
async def new_request(
    job_id: int,
    user: Annotated[User, Security(get_current_user, scopes=Scopes.seeker)],
):
    try:
        seeker = user.seeker
        JobRequest.create(
            job=Job.get_by_id(job_id),
            seeker=seeker,
            expire_on=datetime.now() + timedelta(30),
        )
    except DoesNotExist:
        raise HTTPException(status.HTTP_400_BAD_REQUEST)


@router.get("/")
async def get_requests(
    user: Annotated[User, Security(get_current_user)],
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(le=50, ge=1)] = 10,
) -> JobRequestPage:
    if user.role == Role.employer:
        employer = user.employer
        query = (
            JobRequest.select()
            .join(Job)
            .join(Employer)
            .where(Employer.id == employer.id)
            .order_by(-JobRequest.created_on)
            .paginate(page, per_page)
        )
    elif user.role == Role.seeker:
        seeker = user.seeker
        query = (
            JobRequest.select()
            .where(JobRequest.seeker == seeker.id)
            .order_by(-JobRequest.created_on)
            .paginate(page, per_page)
        )
    else:
        raise Exception("Unknown user?!")

    count = query.count()
    if count == 0:
        raise HTTPException(status.HTTP_204_NO_CONTENT)
    pages_count = ceil(count / per_page)
    if page <= pages_count:
        return JobRequestPage(
            meta=PaginationMeta(
                total_count=count,
                per_page=per_page,
                current_page=page,
                page_count=pages_count,
            ),
            requests=[jr.to_schema(JobRequestSchema) for jr in query],
        )
