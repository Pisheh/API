import os
from datetime import datetime, timedelta
from typing import Union, Any
from jose import jwt
from fastapi.middleware import Middleware
from app.models.dbmodel import Seeker, Employer


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


def create_access_token(subject: Seeker | Employer, expires_delta: int = None) -> str:
    role = "seeker" if isinstance(subject, Seeker) else "employer"
    if expires_delta is not None:
        expires_delta = datetime.utcnow() + expires_delta
    else:
        expires_delta = datetime.utcnow() + timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        )
    encoded_jwt = jwt.encode(
        dict(exp=expires_delta, id=subject.id, role=role), JWT_SECRET_KEY, ALGORITHM
    )
    return encoded_jwt


def create_refresh_token(subject: Seeker | Employer, expires_delta: int = None) -> str:
    role = "seeker" if isinstance(subject, Seeker) else "employer"
    if expires_delta is not None:
        expires_delta = datetime.utcnow() + expires_delta
    else:
        expires_delta = datetime.utcnow() + timedelta(
            minutes=REFRESH_TOKEN_EXPIRE_MINUTES
        )

    encoded_jwt = jwt.encode(
        dict(exp=expires_delta, id=subject.id, role=role), JWT_SECRET_KEY, ALGORITHM
    )
    return encoded_jwt


def generate_tokens(
    subject: Seeker | Employer, token_expire: int = None, refresh_token: int = None
) -> dict[str:str]:
    return dict(
        token=create_access_token(subject, token_expire),
        refresh_token=create_refresh_token(subject, token_expire),
    )
