from pydantic import BaseModel, EmailStr
from typing import Literal
from uuid import UUID
from datetime import timedelta
import re

__phone_num_re = re.compile(r"^09(\d{9})$")

Role = Literal["employer", "seeker"]


class PhoneNumber(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(
            pattern=r"^09(\d{9})$",
            examples=["09123456789"],
        )

    @classmethod
    def validate(cls, v):
        if not isinstance(v, str):
            raise TypeError("string required")
        m = __phone_num_re.fullmatch(v)
        if not m:
            raise ValueError("invalid phonenumber format")
        return cls(str(m[1]))

    def __repr__(self):
        return f"PhoneNumber({super().__repr__()})"


class UserInfo(BaseModel):
    email: EmailStr | None
    number: PhoneNumber | None


class LoginInfo(BaseModel):
    email: EmailStr | None
    number: PhoneNumber | None
    password: str
    role: Role


class BasicUserInfo(BaseModel):
    firstname: str
    role: Role


class TokenPayload(BaseModel):
    exp: timedelta
    id: UUID
    role: Role


class NewUser(BaseModel):
    firstname: str
    lastname: str
    email: EmailStr
    password: str
    phone_number: PhoneNumber
    role: Role


class LoginResult(BaseModel):
    token: str
    refresh_token: str
