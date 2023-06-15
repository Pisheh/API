from fastapi import APIRouter
from app.models.schemas import BranchInfo
from app.literals import *

router = APIRouter()


@router.get("cities")
def get_cities() -> list[str]:
    return CITIES


@router.get("branches")
def get_branches() -> list[BranchInfo]:
    return [BranchInfo(**b) for b in BRANCHES]
