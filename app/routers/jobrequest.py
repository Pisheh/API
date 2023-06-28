from fastapi import APIRouter, Path, HTTPException, status, Query, Depends
from math import ceil
from typing import Annotated
from pydantic import PositiveInt
from app.models.schemas import JobsPage, JobSchema, PaginationMeta
from app.models.dbmodel import Job, User, TABLES
from app.deps import get_user_or_none, Scopes

router = APIRouter()
