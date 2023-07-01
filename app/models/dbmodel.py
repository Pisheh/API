from peewee import *
import peewee
from playhouse.shortcuts import model_to_dict
from passlib.hash import pbkdf2_sha256
from enum import Enum
from typing import Union
from hashlib import md5
from peewee import callable_
import datetime
from datetime import timedelta
import pydantic
from .schemas import SkillItem, EmployerSchema, UserSchema, Role, ExamTypes
from typing import Literal
from slugify import slugify
import uuid
import shortuuid
import json
import pydantic

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


def simphash(string: str) -> str:
    return md5(string.encode()).hexdigest()


_default = lambda arg, value: value if arg is DEFAULT else arg


class DBTables(list):
    def add_many_to_many(self, m2m: ManyToManyField):
        m2m: Model
        setattr(self, m2m._meta.table_name, m2m)
        self.append(m2m)


class JsonField(CharField):
    def db_value(self, value):
        if value:
            return json.dumps(value)
        return value

    def python_value(self, value):
        if value:
            return json.loads(value)
        return value


class JsonObjectField(TextField):
    def __init__(
        self, json_schema: pydantic.BaseModel, null: bool = ..., **kwargs
    ) -> None:
        super().__init__(null, **kwargs)
        self.json_schema = json_schema

    def db_value(self, value: pydantic.BaseModel):
        if value in None:
            return None
        elif isinstance(value, self.json_schema):
            return value.json()
        raise ValueError(f"value must be an instance of {type(self.json_schema)}")

    def python_value(self, value: str | None):
        if value:
            return self.json_schema(**json.loads(value))
        return value


class EnumField(FixedCharField):
    def __init__(self, choices: Enum, *args, **kwargs):
        length = max(map(lambda e: len(e.value), choices))
        super(FixedCharField, self).__init__(length, *args, **kwargs)
        self.enum: Enum = choices

    def db_value(self, value):
        return value and str(value.value)

    def python_value(self, value):
        return value and self.enum(value)


class BaseModel(Model):
    _default_schema_: pydantic.main.ModelMetaclass = None

    def __init__(self, *args, **kwargs) -> None:
        if "slug" in self._meta.fields and "slug" not in kwargs:
            slug = self.slugify(self._meta.fields["slug"].max_length, **kwargs)
            if slug:
                kwargs["slug"] = slug
        super().__init__(*args, **kwargs)

    @classmethod
    def slugify(cls, max_len, **kwargs) -> str:
        if "title" in kwargs:
            return slugify(kwargs["title"], max_length=max_len)

    class Meta:
        database = database_proxy
        only_save_dirty = True

    def to_schema(
        self, type_: pydantic.BaseModel = DEFAULT, **kwargs
    ) -> pydantic.BaseModel:
        data = {}
        type_ = _default(type_, self._default_schema_)
        for name, field in type_.__fields__.items():
            if name in kwargs:
                data[name] = kwargs[name]
                continue
            value = getattr(self, name)
            value_type = type(value)
            if isinstance(value, BaseModel):
                value = value.to_schema(field.type_)
            if (
                field in self._meta.manytomany
                or field in self._meta.backrefs
                or isinstance(value, peewee.ModelSelect)
            ):
                l = []
                for v in value:
                    l.append(v.to_schema(field.sub_fields[0].type_))
                if l:
                    value = l
                else:
                    continue
            data[name] = value
        return type_(**data)


TABLES = DBTables()


def add_table(model: Model):
    TABLES.append(model)
    for _, m2m in model._meta.manytomany.items():
        m2m: ManyToManyField
        TABLES.add_many_to_many(m2m.get_through_model())
    return model


@add_table
class JobCategory(BaseModel):
    slug = FixedCharField(100, primary_key=True)
    title = CharField()
    discipline = CharField()
    expertise = CharField()
    min_salary = IntegerField(null=True)
    max_salary = IntegerField(null=True)

    # personalities <> Personality.job_categories
    # jobs < Job.category
    # guides < Guide.category

    @property
    def avg_min_salary(self):
        return self.jobs.select(Job, fn.AVG(Job.min_salary)).scalar()

    @property
    def avg_mav_salary(self):
        return self.jobs.select(Job, fn.AVG(Job.max_salary)).scalar()


@add_table
class Guide(BaseModel):
    slug = FixedCharField(100, primary_key=True)
    title = CharField()
    summary = CharField(null=True)
    basic = TextField()
    advanced = TextField(null=True)
    category = ForeignKeyField(JobCategory, backref="guides")

    @property
    def roadmap(self):
        return self.timeline.select().order_by(SkillTimeline.index)

    # job_category - JobCategory.guide
    # timeline < SkillTimeline.guide


@add_table
class Skill(BaseModel):
    _default_schema_ = SkillItem

    slug = FixedCharField(100, primary_key=True)
    title = CharField()
    description = CharField(null=True)
    exam_scores = JsonField(null=True)

    @property
    def exam(self) -> Union["Exam", None]:
        return self.exams.get_or_none()

    @exam.setter
    def exam(self, value):
        value.skill = self
        value.save(only=[Exam.skill])

    # jobs <> Job.skills
    # exam - Exam
    # seekers < SeekerSkill.skill
    # courses < Course.skill


@add_table
class Course(BaseModel):
    slug = FixedCharField(100, primary_key=True)
    title = CharField()
    description = CharField()
    link = CharField()
    clicks = IntegerField(default=0)
    skill = ForeignKeyField(Skill, backref="courses")


@add_table
class Employer(BaseModel):
    _default_schema_ = EmployerSchema

    co_name = TextField(null=True)
    co_address = TextField(null=True)
    co_phones = JsonField(null=True)
    co_ver_code = TextField(null=True)
    city = FixedCharField(30)

    @property
    def account(self) -> "User":
        return self.account_set.get()

    @account.setter
    def account(self, account_obj):
        account_obj.seeker = self
        account_obj.save(only=[User.seeker])

    @property
    def avatar(self):
        return self.account.avatar

    @property
    def id(self):
        return self.account.id

    # jobs < Job.employer
    # account - User.employer


@add_table
class Seeker(BaseModel):
    # _default_schema_ = SeekerSchema

    firstname = CharField()
    lastname = CharField()
    cv_content = TextField(null=True)

    @property
    def account(self) -> "User":
        return self.account_set.get()

    @account.setter
    def account(self, account_obj):
        account_obj.seeker = self
        account_obj.save(only=[User.seeker])

    @property
    def avatar(self):
        return self.account.avatar

    # exam_results < ExamResult.seeker
    # job_requests < JobRequest.seeker
    # personalities <> Personality.users
    # skills < SeekerSkill.seeker
    # account - User.seeker


@add_table
class User(BaseModel):
    _default_schema_ = UserSchema

    id = FixedCharField(22, default=shortuuid.uuid, primary_key=True)
    avatar = CharField(null=True)
    email = FixedCharField(64, index=True, unique=True)
    phone_number = FixedCharField(9, index=True, unique=True)
    pass_hash = CharField()
    role = EnumField(Role)
    disabled = BooleanField(default=False)
    seeker = ForeignKeyField(Seeker, backref="account_set", null=True)
    employer = ForeignKeyField(Employer, backref="account_set", null=True)
    logged_in = BooleanField(default=False)
    visible = BooleanField(default=True)

    def verify_password(self, password):
        return check_password_hash(self.pass_hash, password)

    @staticmethod
    def hash_password(password):
        return generate_password_hash(password)


@add_table
class SeekerSkill(BaseModel):
    skill = ForeignKeyField(Skill, backref="seekers")
    seeker = ForeignKeyField(Seeker, backref="skills")
    score = IntegerField()

    # exam_results < ExamResult.seeker_skill


@add_table
class Exam(BaseModel):
    title = CharField()
    exam_type = EnumField(ExamTypes)
    personality_test = FixedCharField(10, null=True)
    skill = ForeignKeyField(Skill, backref="exams", unique=True)
    exam_data = JsonField(null=True)

    # questions


@add_table
class ExamQuestion(BaseModel):
    content = CharField()
    exam = ForeignKeyField(Exam, backref="questions")

    # answers


@add_table
class ExamAnswer(BaseModel):
    content = CharField()
    score = FloatField(default=0)
    question = ForeignKeyField(ExamQuestion, backref="answers")


@add_table
class ExamResult(BaseModel):
    exam = ForeignKeyField(Exam)
    seeker = ForeignKeyField(Seeker, backref="exam_results")
    seeker_skill = ForeignKeyField(SeekerSkill, backref="exam_results", null=True)
    data = JsonField()
    score = IntegerField()


class ExamQuestionSchema(pydantic.BaseModel):
    question_id: int
    answers: list[int]


class ExamProcessDataSchema(pydantic.BaseModel):
    questions: list[ExamQuestionSchema]
    user_answers: list[int]


@add_table
class ExamProcess(BaseModel):
    exam = ForeignKeyField(Exam)
    seeker = ForeignKeyField(Seeker, backref="exam_processes")
    created_on = DateTimeField(default=datetime.datetime.now)
    expire_on = DateTimeField(
        null=True
    )  # TODO: Ask stack holders about this field default
    continuable = BooleanField(default=True)
    data = JsonObjectField(ExamProcessDataSchema, null=True)


@add_table
class Job(BaseModel):
    title = CharField()
    description = TextField()
    requirements = JsonField()
    skills = ManyToManyField(Skill, backref="jobs")
    category = ForeignKeyField(JobCategory, backref="jobs", null=True)
    min_salary = IntegerField()
    max_salary = IntegerField()
    created_on = DateTimeField(default=datetime.datetime.now)
    expire_on = DateTimeField()
    expired = BooleanField(False, default=False)
    employer = ForeignKeyField(Employer, backref="jobs")
    day_time = CharField(40)
    type = CharField(40)

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


@add_table
class Personality(BaseModel):
    slug = FixedCharField(21, primary_key=True)
    test = FixedCharField(10)
    model = FixedCharField(10)
    seekers = ManyToManyField(Seeker, "personalities")
    job_categories = ManyToManyField(JobCategory, "personalities")

    @classmethod
    def slugify(cls, max_len, **kwargs):
        if "test" in kwargs and "model" in kwargs:
            return slugify(kwargs["test"] + "-" + kwargs["model"], max_length=max_len)


@add_table
class SkillTimeline(BaseModel):
    title = CharField()
    description = CharField()
    guide = ForeignKeyField(Guide, backref="timeline")
    skill = ForeignKeyField(Skill)
    index = IntegerField()

    @property
    def courses(self):
        return self.skill.courses
