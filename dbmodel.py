from peewee import *
from playhouse.shortcuts import model_to_dict
from passlib.hash import pbkdf2_sha256
from enum import Enum
from typing import Any, Sequence
from hashlib import md5
from peewee import callable_
import datetime
from datetime import timedelta
import pydantic
from schemas import SkillSchema, JobSchema, EmployerSchema
from typing import Literal
from slugify import slugify
import uuid
import shortuuid
import json

generate_password_hash = lambda p: pbkdf2_sha256.using(rounds=8000, salt_size=10).hash(
    p
)
check_password_hash = lambda hash, password: pbkdf2_sha256.using(
    rounds=8000, salt_size=10
).verify(password, hash)
database_proxy = DatabaseProxy()


class Default(object):
    pass


DEFAULT = Default()

HASH_LEN = 32


def simphash(string: str) -> str:
    return md5(string.encode()).hexdigest()


_clone_set = lambda s: set(s) if s else set()
_default = lambda arg, value: value if arg is DEFAULT else arg


class JsonField(CharField):
    def db_value(self, value):
        return json.dumps(value)

    def python_value(self, value):
        return json.loads(value)


class EnumField(IntegerField):
    def __init__(self, choices: Enum, *args, **kwargs):
        super(IntegerField, self).__init__(*args, **kwargs)
        self.choices: Enum = choices

    def db_value(self, value):
        return value.value

    def python_value(self, value):
        return self.choices(value)


class BaseModel(Model):
    _default_schema_: pydantic.main.ModelMetaclass = None

    class Meta:
        database = database_proxy

    def to_schema(self, type_: pydantic.BaseModel = DEFAULT) -> pydantic.BaseModel:
        data = {}
        type_ = _default(type_, self._default_schema_)
        for name, field in type_.__fields__.items():
            value = getattr(self, name)
            value_type = type(value)
            if isinstance(value, BaseModel):
                value = value.to_schema(field.type_)
            if name in self._meta.manytomany or name in self._meta.backrefs:
                l = []
                for v in value:
                    l.append(v.to_schema(field.sub_fields[0].type_))
                value = l
            data[name] = value
        return type_(**data)


TABLES = []


def add_table(model: Model):
    TABLES.append(model)
    for _, m2m in model._meta.manytomany.items():
        m2m: ManyToManyField
        TABLES.append(m2m.get_through_model())
    return model


@add_table
class Guide(BaseModel):
    slug = FixedCharField(64, primary_key=True)
    title = CharField()
    summary = CharField(null=True)
    basic = TextField()
    advanced = TextField(null=True)
    branch = FixedCharField(64, index=True)
    expertise = FixedCharField(64, index=True)

    # personalities <> Personality.guides
    # job_category - JobCategory.guide
    # skills <> Skill.guides


@add_table
class Skill(BaseModel):
    _default_schema_ = SkillSchema

    slug = FixedCharField(64, primary_key=True)
    title = CharField()
    description = CharField(null=True)
    guides = ManyToManyField(Guide, backref="guides")
    exam_scores = JsonField()

    # jobs <> Job.skills
    # exams < Exam
    # seekers < SeekerSkill.skill
    # courses < Course.skill


@add_table
class Course(BaseModel):
    slug = FixedCharField(64, primary_key=True)
    title = CharField()
    description = CharField()
    skill = ForeignKeyField(Skill, backref="courses")
    link = CharField()
    clicks = IntegerField()


@add_table
class JobCategory(BaseModel):
    slug = FixedCharField(64, primary_key=True)
    title = CharField()
    total_min_salary = IntegerField()
    total_max_salary = IntegerField()
    count_salary = IntegerField()
    guide = ForeignKeyField(Guide, backref="job_category")

    # personalities <> Personality.job_cats
    # jobs < Job.category

    @property
    def avg_min_salary(self):
        return self.total_min_salary / self.count_salary

    @property
    def avg_mav_salary(self):
        return self.total_max_salary / self.count_salary


class User(BaseModel):
    id = FixedCharField(22, default=shortuuid.uuid, primary_key=True)
    avatar = CharField(null=True)
    email = FixedCharField(64, index=True)
    phone_number = FixedCharField(9, index=True)
    pass_hash = CharField()
    # job_requests

    def verify_password(self, password):
        return check_password_hash(self.pass_hash, password)

    def set_password(self, password):
        self.pass_hash = generate_password_hash(password)

    @staticmethod
    def hash_password(password):
        return generate_password_hash(password)


@add_table
class Employer(User):
    _default_schema_ = EmployerSchema
    co_name = TextField(null=True)
    co_address = TextField(null=True)
    co_phones = JsonField(null=True)
    co_ver_code = TextField(null=True)
    city = FixedCharField(30)
    # jobs


@add_table
class Seeker(User):
    firstname = CharField(null=True)
    lastname = CharField(null=True)
    cv_content = TextField(null=True)

    # exam_results < ExamResult.seeker
    # job_requests < JobRequest.seeker
    # personalities <> Personality.users
    # skills < SeekerSkill.seeker


@add_table
class Personality(BaseModel):
    slug = FixedCharField(32, primary_key=True)
    name = FixedCharField(32)
    description = CharField()
    users = ManyToManyField(Seeker, backref="personalities")
    job_cats = ManyToManyField(JobCategory, backref="personalities")
    guides = ManyToManyField(Guide, backref="personalities")

    # exams < Exam.personality


@add_table
class SeekerSkill(BaseModel):
    skill = ForeignKeyField(Skill, backref="seekers")
    seeker = ForeignKeyField(Seeker, backref="skills")
    score = IntegerField()

    # exam_results < ExamResult.seeker_skill


@add_table
class Exam(BaseModel):
    class Types(Enum):
        SKILL = 0
        PERSONALITY = 1

    title = CharField()
    type = EnumField(Types)
    skill = ForeignKeyField(Skill, backref="exams")
    personality = ForeignKeyField(Personality, backref="exams")

    # questions < Question.exam


@add_table
class Question(BaseModel):
    exam = ForeignKeyField(Exam, backref="questions")
    content = CharField()

    # answers < Answer.question


@add_table
class Answer(BaseModel):
    question = ForeignKeyField(Question, backref="answers")
    content = CharField()
    score = FloatField()


@add_table
class ExamResult(BaseModel):
    exam = ForeignKeyField(Exam)
    seeker = ForeignKeyField(Seeker, backref="exam_results")
    seeker_skill = ForeignKeyField(SeekerSkill, backref="exam_results", null=True)
    data = JsonField()
    score = IntegerField()


@add_table
class Job(BaseModel):
    title = CharField()
    description = TextField()
    requirements = JsonField()
    skills = ManyToManyField(Skill, backref="jobs")
    category = ForeignKeyField(JobCategory, backref="jobs")
    min_salary = IntegerField()
    max_salary = IntegerField()
    created_on = DateTimeField(default=datetime.datetime.now)
    expire_on = DateTimeField()
    expired = BooleanField(False, default=False)
    employer = ForeignKeyField(Employer, backref="jobs")

    # requests < JobRequests.job

    @property
    def salary(self) -> dict[str:int] | None:
        if self.min_salary == 0 or self.max_salary == 0:
            return
        return dict(min=self.min_salary, max=self.max_salary)

    @property
    def timedelta(self):
        delta: timedelta = datetime.datetime.now() - self.created_on
        unit = "مدت‌ها پیش"
        amount = 0
        if delta.days < 1:
            if delta.seconds < 10 * 60:
                unit = "به تازگی"
            elif delta.seconds // 60 < 25:
                unit = "دقایقی پیش"
            elif delta.seconds // 60 < 35:
                unit = "نیم‌ساعت پیش"
            elif delta.seconds // 60 < 60:
                unit = "دقیقه پیش"
                amount = delta.seconds // 60
            elif delta.seconds // 3600 < 10:
                unit = "ساعت پیش"
                amount = delta.seconds // 3600
            elif delta.seconds // 3600 < 24:
                unit = "امروز"
        if delta.days == 1:
            unit = "دیروز"
        elif 1 < delta.days < 7:
            unit = "روز پیش"
            amount = delta.days
        elif 1 <= delta.days < 30:
            unit = "هفته قبل"
            amount = delta.days // 7
        elif 1 <= delta.days // 30 < 12:
            unit = "ماه پیش"
            amount = delta.days // 30
        return dict(unit=unit, amount=amount)


@add_table
class JobRequest(BaseModel):
    job = ForeignKeyField(Job, backref="requests")
    seeker = ForeignKeyField(Seeker, backref="job_requests")
    created_on = DateTimeField(default=datetime.datetime.now)
    expire_on = DateTimeField(default=datetime.datetime.now)
    expired = BooleanField(False, default=False)

    @classmethod
    def get(cls, *query, **filters):
        res = super().get(*query, **filters)
        if res.expire_on <= datetime.datetime.now():
            res.expired = True

        return res


TABLES = (
    Exam,
    Question,
    Answer,
    Skill,
    SeekerSkill,
    JobSkill,
    Seeker,
    Employer,
    Job,
    Personality.users.get_through_model(),
    Personality.job_cats.get_through_model(),
    Personality.guides.get_through_model(),
)
