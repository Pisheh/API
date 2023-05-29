from peewee import *
from playhouse.shortcuts import model_to_dict
from werkzeug.security import generate_password_hash, check_password_hash
from enum import Enum
from typing import Sequence
from hashlib import md5
import datetime

database_proxy = DatabaseProxy()

DEFAULT = object()

HASH_LEN = 32


def simphash(string: str) -> str:
    return md5(string.encode()).hexdigest()


class BaseMeta:
    database = database_proxy


class BaseModel(Model):
    _recurse = True
    _exclude = None
    _include = None
    _backrefs = True

    class Meta(BaseMeta):
        pass

    def to_dict(
        self,
        recurse: bool | DEFAULT = DEFAULT,
        backrefs: bool | DEFAULT = DEFAULT,
        only: None | Sequence[str] = None,
        exclude: DEFAULT | None | Sequence[str] = DEFAULT,
        extra_attrs: DEFAULT | None | Sequence[str] = DEFAULT,
        max_depth: None | int = None,
        update: dict = {},
    ):
        """
        Convert a model instance (and any related objects) to a dictionary.

        :param bool recurse: Whether foreign-keys should be recursed.
        :param bool backrefs: Whether lists of related objects should be recursed.
        :param only: A list (or set) of field instances indicating which fields
            should be included.
        :param exclude: A list (or set) of field instances that should be
            excluded from the dictionary.
        :param list extra_attrs: Names of model instance attributes or methods
            that should be included.
        :param int max_depth: Maximum depth to recurse, value <= 0 means no max.
        :param dict update: A dictionary of custom key/values.
        """

        res = model_to_dict(
            self,
            recurse=self._recurse if recurse is DEFAULT else recurse,
            backrefs=self._backrefs if backrefs is DEFAULT else backrefs,
            only=only,
            exclude=self._exclude if exclude is DEFAULT else exclude,
            extra_attrs=self._include if extra_attrs is DEFAULT else extra_attrs,
            max_depth=max_depth,
        )
        res.update(**update)
        return res


class Exam(BaseModel):
    _recurse = False
    _backrefs = True

    title = CharField()
    skill = ForeignKeyField("Skill", backref="exams")
    # questions


class Question(BaseModel):
    _recurse = False
    _backrefs = True

    exam = ForeignKeyField(Exam, backref="questions")
    content = CharField()
    # answers


class Answer(BaseModel):
    _recurse = False
    _exclude = ["correct_score", "incorrect_score"]

    question = ForeignKeyField(Question, backref="answers")
    content = CharField()
    correct_score = IntegerField(default=0)
    incorrect_score = IntegerField(default=0)


class Skill(BaseModel):
    _backrefs = False  # exclude exams, seekers and jobs

    title = CharField()
    desc = CharField(null=True)
    # exams
    # seekers
    # jobs


class SkillExam(BaseModel):
    exam = ForeignKeyField(Exam, backref="skills")
    skill = ForeignKeyField(Skill, backref="exams")


class __user(BaseModel):
    class Meta(BaseMeta):
        indexes = (("email", "email_hash"), True)

    _exclude = ["_email_hash", "pass_hash", "job_requests"]

    firstname = CharField(null=True)
    lastname = CharField(null=True)
    _email = FixedCharField(320, column_name="email")
    _email_hash = FixedCharField(HASH_LEN, index=True, column_name="email_hash")
    pass_hash = CharField()
    # job_requests

    @property
    def email(self):
        return self._email

    @email.setter
    def email_set(self, value):
        self._email = value
        self._email_hash = simphash(value)

    def get_by_email(self, email: str):
        return self.get(self._email == email, self._email_hash == simphash(email))

    def verify_password(self, password):
        check_password_hash(self.pass_hash, password)

    def set_password(self, password):
        self.pass_hash = generate_password_hash(password)


class Employer(__user):
    co_name = TextField()
    co_address = TextField(null=True)
    co_phones = TextField(null=True)
    co_ver_code = TextField()
    # jobs


class Seeker(__user):
    phone_number = TextField()
    cv_content = TextField()
    # skills


class SkillSeeker(BaseModel):
    seeker = ForeignKeyField(Seeker, backref="skills")
    skill = ForeignKeyField(Skill, backref="seekers")
    score = IntegerField()


class Job(BaseModel):
    _exclude = ["requests"]
    title = TextField()
    content = TextField()
    min_salary = IntegerField()
    max_salary = IntegerField()
    created_on = DateTimeField(default=datetime.datetime.now)
    expire_on = DateTimeField()
    expired = BooleanField(False, Default=False)
    employer = ForeignKeyField(Employer, backref="jobs")
    # skills
    # requests

    @classmethod
    def get(cls, *query, **filters):
        res = super().get(*query, **filters)
        if res.expire_on <= datetime.datetime.now():
            res.expired = True

        return res


class JobSkill(BaseModel):
    jop = ForeignKeyField(Job, backref="skills")
    skill = ForeignKeyField(Skill, backref="jobs")


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


TABLES = (Exam, Question, Answer, Skill, SkillSeeker, JobSkill, Seeker, Employer, Job)
