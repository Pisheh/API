from pydantic import EmailStr, validator, PositiveInt, Field
from fastapi_utils.api_model import APIModel as BaseModel
from pydantic.fields import ModelField
from typing import Literal, ForwardRef
from uuid import UUID
from datetime import timedelta, datetime
from enum import Enum
import re

__phone_num_re = re.compile(r"^09(\d{9})$")


class ExamTypes(str, Enum):
    skill = "skill"
    personality = "personality"


class Role(str, Enum):
    seeker = "seeker"
    employer = "employer"


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
            raise ValueError("invalid phone number format")
        return cls(str(m[1]))

    def __repr__(self):
        return f"PhoneNumber({super().__repr__()})"


class UserQuery(BaseModel):
    email: EmailStr = None
    phone_number: PhoneNumber = None


class LoginInfo(BaseModel):
    email: EmailStr = None
    phone_number: PhoneNumber
    password: str


class UserQueryResult(BaseModel):
    firstname: str = None
    lastname: str = None
    co_name: str = None
    role: Role


class EmployerInfo(BaseModel):
    co_name: str
    city: str
    avatar: str


# JobSchema = ForwardRef("JobSchema")


class EmployerSchema(BaseModel):
    co_name: str
    city: str
    avatar: str
    jobs: list["JobSchema"]


class SkillItem(BaseModel):
    slug: str
    title: str = None
    description: str = None


class SeekerInfo(BaseModel):
    firstname: str
    lastname: str
    avatar: str
    skills: list[SkillItem] = None


class UserSchema(BaseModel):
    id: str
    avatar: str = None
    email = EmailStr
    phone_number = PhoneNumber
    role: Role
    employer: EmployerInfo | None = None
    seeker: SeekerInfo | None = None


class SignupInfo(BaseModel):
    email = EmailStr
    phone_number = PhoneNumber
    password: str
    role: Role
    employer: EmployerInfo = None
    seeker: SeekerInfo = None


class LoginResult(BaseModel):
    token: str
    user_info: UserSchema


class Answer(BaseModel):
    id: int
    content: str


class Question(BaseModel):
    id: int
    content: str
    answers: list[Answer]


class ExamInfo(BaseModel):
    id: int
    title: str


class ExamSchema(BaseModel):
    id: int
    title: str
    questions: list[Question]


class CourseSchema(BaseModel):
    slug: str
    title: str
    description: str
    link: str


class GuideItem(BaseModel):
    slug: str
    title: str
    summary: str
    branch: str
    expertise: str
    recommended: bool = False


class SkillSchema(BaseModel):
    slug: str
    title: str
    description: str = None
    courses: list[CourseSchema]
    guide: GuideItem
    exams: list[ExamInfo]


class TokenData(BaseModel):
    exp: timedelta
    id: str
    scopes: list[str] = []


class TimeDelta(BaseModel):
    unit: Literal[
        "مدت‌ها پیش",
        "به تازگی",
        "دقایقی پیش",
        "نیم‌ساعت پیش",
        "دقیقه پیش",
        "ساعت پیش",
        "امروز",
        "دیروز",
        "روز پیش",
        "هفته قبل",
        "ماه پیش",
    ]
    amount: int = Field(ge=0)


class Salary(BaseModel):
    min: int
    max: int


class JobCategoryInfo(BaseModel):
    slug: str
    title: str


class JobSchema(BaseModel):
    id: int = Field(ge=1)
    title: str
    description: str
    salary: Salary = None
    created_on: datetime
    employer: EmployerInfo
    requirements: list[str]
    skills: list[SkillItem]
    timedelta: TimeDelta
    category: JobCategoryInfo


# JobSchema.update_forward_refs()


class PaginationMeta(BaseModel):
    total_count: PositiveInt
    page_count: PositiveInt
    current_page: PositiveInt
    per_page: PositiveInt


class JobsPage(BaseModel):
    meta: PaginationMeta
    jobs: list[JobSchema]


class GuidesPage(BaseModel):
    meta: PaginationMeta
    guides: list[GuideItem]


class BranchInfo(BaseModel):
    branch: str
    expertise: list[str]


class GuideSchema(BaseModel):
    slug: str
    title: str
    summary: str
    branch: str
    expertise: str
    basic: str
    advanced: str = None
    skills: list[SkillSchema] = []
