from pydantic import EmailStr, validator, PositiveInt, Field
from fastapi_utils.api_model import APIModel as BaseModel
from pydantic.fields import ModelField
from typing import Literal, ForwardRef
from uuid import UUID
from datetime import timedelta, datetime
from enum import Enum
import re

phone_num_re = re.compile(r"^09\d{9}$")


class ExamTypes(str, Enum):
    skill = "skill"
    personality = "personality"


class Role(str, Enum):
    seeker = "seeker"
    employer = "employer"


class ForeignGuideMotivation(str, Enum):
    education = "education"
    work = "work"
    both = "both"


class PhoneNumber(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(
            pattern=r"^09\d{9}$",
            examples=["09123456789"],
        )

    @classmethod
    def validate(cls, v):
        if not isinstance(v, str):
            raise TypeError("string required")
        m = phone_num_re.fullmatch(str(v))
        if not m:
            raise ValueError("invalid phone number format")
        return str(m[0])

    def __repr__(self):
        return f"PhoneNumber({super().__repr__()})"


class Username(str):
    email_pattern = re.compile(
        r"[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*@(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?"
    )
    phone_pattern = re.compile(r"09\d{9}")

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(
            examples=["09123456721", "example21@example.com"],
        )

    @classmethod
    def validate(cls, v):
        if not isinstance(v, str):
            raise TypeError("string required")
        email_match = cls.email_pattern.fullmatch(v)
        phone_match = cls.phone_pattern.fullmatch(v)

        if email_match or phone_match:
            return v
        else:
            raise ValueError("invalid format")

    def __repr__(self):
        return f"Username({super().__repr__()})"


class UserQuery(BaseModel):
    username: Username


class LoginInfo(BaseModel):
    username: Username = Field(
        example="email:example21@example.com",
        description="username that starts with `email:` or `phone:`, E.g: `phone:09123456721`",
    )
    password: str = Field(example="password21")


class UserQueryResult(BaseModel):
    firstname: str = None
    lastname: str = None
    co_name: str = None
    role: Role


class EmployerInfo(BaseModel):
    id: str
    co_name: str
    city: str
    avatar: str | None


# JobSchema = ForwardRef("JobSchema")


class PersonalitySchema(BaseModel):
    slug: str
    test: str
    model: str


class EmployerSchema(BaseModel):
    co_name: str
    co_address: str
    co_phones: str
    co_ver_code: str
    city: str
    avatar: str | None = None


class SkillItem(BaseModel):
    slug: str
    title: str = None
    description: str = None


class SeekerInfo(BaseModel):
    firstname: str
    lastname: str
    skills: list[SkillItem] = None


class UserSchema(BaseModel):
    id: str
    avatar: str = None
    role: Role
    employer: EmployerInfo | None = None
    seeker: SeekerInfo | None = None


class MyInfoSchema(BaseModel):
    id: str
    avatar: str = None
    email: EmailStr
    phone_number: PhoneNumber
    role: Role
    employer: EmployerInfo | None = None
    seeker: SeekerInfo | None = None


# update me
class UpdateEmployerInfo(BaseModel):
    co_name: str
    city: str


class UpdateSeekerInfo(BaseModel):
    firstname: str
    lastname: str


class UpdateUserInfo(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    password_confirm: str = Field(min_length=8)
    phone_number: PhoneNumber
    employer: UpdateEmployerInfo | None = None
    seeker: UpdateSeekerInfo | None = None


# ------------------------


class SignupInfo(BaseModel):
    email = EmailStr
    phone_number = PhoneNumber
    password: str
    role: Role
    employer: EmployerInfo = None
    seeker: SeekerInfo = None


class LoginResult(BaseModel):
    access_token: str = Field(alias="access_token")
    refresh_token: str = Field(alias="refresh_token")
    sudo_token: str
    user_info: UserQueryResult


class SudoToken(BaseModel):
    sudo_token: str


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


class SkillSchema(BaseModel):
    slug: str
    title: str
    description: str = None
    courses: list[CourseSchema]
    exam: ExamInfo | None


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


class JobCategorySchema(BaseModel):
    slug: str
    title: str
    course: str
    expertise: str
    min_salary: int | None
    max_salary: int | None
    guides: list["GuideItem"] = []


class PaginationMeta(BaseModel):
    total_count: PositiveInt
    page_count: PositiveInt
    current_page: PositiveInt
    per_page: PositiveInt


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
    category: JobCategorySchema
    type: str = Field(example="تمام وقت")
    day_time: str = Field(example="شنبه تا چهارشنبه ۸ الی ۱۴")


class JobsPage(BaseModel):
    meta: PaginationMeta
    jobs: list[JobSchema]


class GuidesPage(BaseModel):
    meta: PaginationMeta
    guides: list[GuideItem]


class BranchInfo(BaseModel):
    branch: str
    expertise: list[str]


class SkillsTimeline(BaseModel):
    title: str
    description: str
    skill: SkillSchema
    index: int


class GuideSchema(BaseModel):
    slug: str
    title: str
    summary: str
    basic: str
    advanced: str = None
    category: JobCategorySchema
    roadmap: list[SkillsTimeline] = []


class CategoryPage(BaseModel):
    meta: PaginationMeta
    categories: list[JobCategorySchema]


class JobRequestSchema(BaseModel):
    id: int
    job: JobSchema
    seeker: SeekerInfo
    expire_on: datetime


class JobRequestPage(BaseModel):
    meta: PaginationMeta
    requests: list[JobRequestSchema]
