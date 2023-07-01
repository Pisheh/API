from fastapi import APIRouter, Path, HTTPException, status
from fastapi.responses import RedirectResponse
from math import ceil
from typing import Annotated
from pydantic import PositiveInt
from app.models.schemas import JobsPage, JobSchema, PaginationMeta
from app.models.dbmodel import Course
from app.deps import get_user_or_none, Scopes
from peewee import DoesNotExist

router = APIRouter()


@router.get(
    "/{slug}",
    response_class=RedirectResponse,
    response_description="Redirect to course link",
)
async def get_course(slug: Annotated[str, Path]):
    try:
        course = Course.get_by_id(slug)
        course.clicks += 1
        course.save()
        return RedirectResponse(course.link)
    except DoesNotExist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="course.not_found"
        )
