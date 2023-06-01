from pydantic import BaseModel, EmailStr, validator, PositiveInt, Field
from pydantic.fields import ModelField
from typing import Literal
from uuid import UUID
from datetime import timedelta, datetime
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


class UserSchema(BaseModel):
    uuid: str
    avatar: str | None
    email = EmailStr
    phone_number = PhoneNumber


class EmployerSummary(UserSchema):
    co_name: str


class EmployerSchema(UserSchema):
    co_name: str
    jobs: list["JobSchema"]


class UserInfo(BaseModel):
    email: EmailStr | None
    number: PhoneNumber | None


class LoginInfo(BaseModel):
    email: EmailStr | None
    number: PhoneNumber | None
    password: str
    role: Role


class SkillSchema(BaseModel):
    id: int = Field(ge=1)
    title: str
    desc: str | None


class BasicUserInfo(BaseModel):
    firstname: str
    role: Role


class TokenPayload(BaseModel):
    exp: timedelta
    id: str
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


class JobSchema(BaseModel):
    id: int = Field(ge=1)
    title: str
    content: str
    min_salary: int
    max_salary: int
    created_on: datetime
    employer: EmployerSummary
    skills: list[SkillSchema]


class PaginationMeta(BaseModel):
    total_count: PositiveInt
    page_count: PositiveInt
    current_page: PositiveInt
    per_page: PositiveInt


class Jobs(BaseModel):
    meta: PaginationMeta
    jobs: list[JobSchema]


class PageRequest(BaseModel):
    page: PositiveInt | None = 1
    per_page: PositiveInt | None = 30

    @validator("per_page")
    def per_page_limit(cls, v):
        assert v <= 100, "perPage out of limitation"
        return v

    @validator("page")
    def page_limit(cls, v):
        assert v
