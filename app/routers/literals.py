from fastapi import APIRouter
from app.literals import *

router = APIRouter()


@router.get("cities")
def get_cities() -> list["str"]:
    return CITIES


@router.get("branches")
def get_branches() -> dict[str : list[str]]:
    return BRANCHES
