from typing import Union, Any, Literal, Annotated
from datetime import datetime
from fastapi import Depends, HTTPException, status, Security
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from jose import jwt, JWTError
from pydantic import ValidationError
from peewee import DoesNotExist
from enum import Enum

from app.utils import ALGORITHM, JWT_SECRET_KEY
from app.models.dbmodel import User
from app.models.schemas import TokenData

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/login",
    scheme_name="JWT",
    scopes={
        "employer": "Get access to employers panel",
        "seeker": "Get access to seekers panel",
        "me": "Read information about the current user",
        "admin": "have access to anything",
    },
)


class Scopes(list, Enum):
    me = ["me"]
    employer = ["employer"]
    seeker = ["seeker"]
    admin = ["admin"]


async def get_current_user(
    security_scopes: SecurityScopes, token: Annotated[str, Depends(oauth2_scheme)]
):
    if security_scopes.scopes:
        authenticate_value = f'Bearer scope="{security_scopes.scope_str}"'
    else:
        authenticate_value = "Bearer"
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": authenticate_value},
    )
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
        token_data = TokenData(**payload)
        if datetime.fromtimestamp(token_data.exp) < datetime.now():
            raise credentials_exception
        user = User.get_by_id(token_data.id)
        if user.disabled:
            raise HTTPException(status_code=400, detail="Inactive user")
        for scope in security_scopes.scopes:
            if scope not in token_data.scopes:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Not enough permissions",
                    headers={"WWW-Authenticate": authenticate_value},
                )
        return user
    except (JWTError, ValidationError, DoesNotExist):
        raise credentials_exception


async def get_user_or_none(
    security_scopes: SecurityScopes,
    token: Annotated[str, Depends(oauth2_scheme)] = None,
):
    if not token:
        return None

    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
        token_data = TokenData(**payload)
        if datetime.fromtimestamp(token_data.exp) < datetime.now():
            return None
        user = User.get_by_id(token_data.id)
        if user.disabled:
            return None
        for scope in security_scopes.scopes:
            if scope not in token_data.scopes:
                return None
        return user
    except (JWTError, ValidationError, DoesNotExist):
        return None
