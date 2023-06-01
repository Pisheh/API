from typing import Union, Any, Literal
from datetime import datetime
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from .utils import ALGORITHM, JWT_SECRET_KEY

from jose import jwt
from pydantic import ValidationError
from .dbmodel import Employer, Seeker
from .schemas import TokenPayload

reuseable_oauth = OAuth2PasswordBearer(tokenUrl="/login", scheme_name="JWT")


def auth(role: Literal["seeker", "employer", "*"]):
    async def get_current_user(token: str = Depends(reuseable_oauth)) -> Employer:
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
            token_data = TokenPayload(**payload)

            if datetime.fromtimestamp(token_data.exp) < datetime.now():
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token expired",
                    headers={"WWW-Authenticate": "Bearer"},
                )
        except (jwt.JWTError, ValidationError):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if token_data.role == "employer" and role == "employer" or role == "*":
            user: Employer | None = Employer.get_or_none(id=token_data.id)
        elif token_data.role == "seeker" and role == "seeker" or role == "*":
            user: Seeker | None = Seeker.get_or_none(id=token_data.id)
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Could not find user",
            )

        return user

    return get_current_user
