import os
from datetime import datetime, timedelta
from typing import Union, Any
from jose import jwt
from fastapi.middleware import Middleware
from app.models.dbmodel import User
from app.models.schemas import TokenData


ACCESS_TOKEN_EXPIRE_MINUTES = 30  # 30 minutes
REFRESH_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days
ALGORITHM = "HS256"
JWT_SECRET_KEY = os.environ.get(
    "JWT_SECRET_KEY", "a not secure secret key because I needed it in github action"
)  # should be kept secret
JWT_REFRESH_SECRET_KEY = os.environ.get(
    "JWT_REFRESH_SECRET_KEY",
    "a not secure secret key because I needed it in github action",
)  # should be kept secret


def create_access_token(user: User, expires_delta: timedelta = None) -> str:
    if expires_delta is not None:
        expires_delta = datetime.utcnow() + expires_delta
    else:
        expires_delta = datetime.utcnow() + timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        )
    encoded_jwt = jwt.encode(
        TokenData(exp=expires_delta, id=user.id, scopes=[user.role.value, "me"]),
        JWT_SECRET_KEY,
        ALGORITHM,
    )
    return encoded_jwt
