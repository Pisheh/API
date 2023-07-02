from peewee import DoesNotExist
from app.models.dbmodel import Exam
from fastapi import APIRouter, Query, HTTPException, status
from typing import Annotated

router = APIRouter()


@router.get("/{id}")
async def get_exam(id: Annotated[int, Query()]):
    try:
        Exam.get_by_id(id)
    except DoesNotExist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
