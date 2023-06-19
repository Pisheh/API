from fastapi import APIRouter, Query, Depends
from typing import Annotated, Any
from app.models.dbmodel import User
from app.deps import get_user_or_none, Scopes

router = APIRouter()


@router.get("/category/search")
async def search_category(
    branch: Annotated(str, Query()) = None,
    expertise: Annotated(str, Query()) = None,
    min_salary: Annotated(int, Query(ge=1)) = None,
    max_salary: Annotated(int, Query(ge=1)) = None,
    user: Annotated(User | None, Depends(get_user_or_none(Scopes.seeker))) = None,
) -> Any:
    ...
