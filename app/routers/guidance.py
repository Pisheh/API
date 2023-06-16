from fastapi import APIRouter, Depends, Query, Path, HTTPException, status, Security
from app.deps import get_user_or_none, Scopes
from typing import Annotated, Literal
from app.models.dbmodel import Guide, User
from app.models.schemas import GuideItem, GuideSchema, Role, GuidesPage, PaginationMeta
from ordered_set import OrderedSet
from peewee import IntegrityError
from pydantic import PositiveInt
from math import ceil

router = APIRouter()


@router.get("/")
async def get_guides(
    page: Annotated(PositiveInt, Query()) = None,
    per_page: Annotated(PositiveInt, Query()) = None,
) -> list[GuideItem]:
    guides_count = Guide.select().count()
    pages_count = ceil(guides_count / per_page)
    if page <= pages_count:
        return GuidesPage(
            meta=PaginationMeta(
                total_count=guides_count,
                current_page=page.page,
                page_count=pages_count,
                per_page=page.per_page,
            ),
            guides=[
                guide.to_schema(GuideItem)
                for guide in Guide.select().pagination(page, per_page)
            ],
        )
    else:
        HTTPException(400, "Guides.bad_pagination")


@router.get("/{slug}")
async def get_guide(slug: Annotated[str, Path()]) -> GuideSchema:
    try:
        return Guide.get(Guide.slug == slug).to_schema(GuideSchema)
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="guide.not_found"
        )
