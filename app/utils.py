import os
from datetime import datetime, timedelta
from jose import jwt
from app.models.dbmodel import User
from pydantic import BaseModel


ACCESS_TOKEN_EXPIRE_TIME = timedelta(hours=12)
REFRESH_TOKEN_EXPIRE_TIME = timedelta(days=3)

ALGORITHM = "HS256"
JWT_SECRET_KEY = os.environ.get(
    "JWT_SECRET_KEY", "a not secure secret key because I needed it in github action"
)  # should be kept secret
JWT_REFRESH_SECRET_KEY = os.environ.get(
    "JWT_REFRESH_SECRET_KEY",
    "a not secure secret key because I needed it in github action",
)  # should be kept secret


class AccessTokenData(BaseModel):
    id: str
    pass_hash: str
    exp: datetime
    scopes: list[str] = []


class RefreshTokenData(BaseModel):
    id: str
    exp: datetime


def create_access_token(user: User, expires_delta: timedelta = None) -> str:
    if expires_delta is not None:
        expires_delta = datetime.utcnow() + expires_delta
    else:
        expires_delta = datetime.utcnow() + ACCESS_TOKEN_EXPIRE_TIME
    encoded_jwt = jwt.encode(
        AccessTokenData(
            id=user.id,
            pass_hash=user.pass_hash,
            exp=expires_delta,
            scopes=[user.role.value, "me"],
        ).dict(),
        JWT_SECRET_KEY,
        ALGORITHM,
    )
    return encoded_jwt


def create_refresh_token(user: User, expires_delta: timedelta = None) -> str:
    if expires_delta is not None:
        expires_delta = datetime.utcnow() + expires_delta
    else:
        expires_delta = datetime.utcnow() + REFRESH_TOKEN_EXPIRE_TIME
    encoded_jwt = jwt.encode(
        RefreshTokenData(exp=expires_delta, id=user.id).dict(),
        JWT_REFRESH_SECRET_KEY,
        ALGORITHM,
    )
    return encoded_jwt
