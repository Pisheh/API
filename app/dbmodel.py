from peewee import *
from playhouse.shortcuts import model_to_dict
from passlib.hash import pbkdf2_sha256
from enum import Enum
from typing import Any, Sequence
from hashlib import md5
from peewee import callable_
from uuid import uuid4
import datetime

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


class BaseModel(Model):
    _recurse_ = True
    _exclude_ = None
    _include_ = None
    _backrefs_ = True

    class Meta:
        database = database_proxy

    def to_dict(
        self,
        recurse=DEFAULT,
        backrefs=DEFAULT,
        only=None,
        exclude=DEFAULT,
        seen=None,
        extra_attrs=DEFAULT,
        fields_from_query=None,
        max_depth=None,
        manytomany=False,
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
        :param SelectQuery fields_from_query: Query that was source of model. Take
            fields explicitly selected by the query and serialize them.
        :param int max_depth: Maximum depth to recurse, value <= 0 means no max.
        :param bool manytomany: Process many-to-many fields.
        """
        _recurse = _default(recurse, self._recurse_)
        _backrefs = _default(backrefs, self._backrefs_)
        _extra_attrs = _clone_set(_default(extra_attrs, self._include_))
        _exclude = _default(exclude, self._exclude_)

        max_depth = -1 if max_depth is None else max_depth
        if max_depth == 0:
            _recurse = False

        only = _clone_set(only)
        should_skip = lambda n: (n in _exclude) or (only and (n not in only))

        if fields_from_query is not None:
            for item in fields_from_query._returning:
                if isinstance(item, Field):
                    only.add(item)
                elif isinstance(item, Alias):
                    _extra_attrs.add(item._alias)

        data = {}
        _exclude = _clone_set(_exclude)
        seen = _clone_set(seen)
        _exclude |= seen
        model_class = type(self)

        if manytomany:
            for name, m2m in self._meta.manytomany.items():
                if should_skip(name):
                    continue

                _exclude.update((m2m, m2m.rel_model._meta.manytomany[m2m.backref]))
                for fkf in m2m.through_model._meta.refs:
                    _exclude.add(fkf)

                accum = []
                for rel_obj in getattr(self, name):
                    accum.append(
                        rel_obj.to_dict(
                            recurse=recurse,
                            backrefs=backrefs,
                            only=only,
                            exclude=exclude,
                            max_depth=max_depth - 1,
                        )
                    )
                data[name] = accum

        for field in self._meta.sorted_fields:
            if should_skip(field):
                continue

            field_data = self.__data__.get(field.name)
            if isinstance(field, ForeignKeyField) and _recurse:
                if field_data is not None:
                    seen.add(field)
                    rel_obj = getattr(self, field.name)
                    field_data = rel_obj.to_dict(
                        recurse=recurse,
                        backrefs=backrefs,
                        only=only,
                        exclude=exclude,
                        seen=seen,
                        max_depth=max_depth - 1,
                    )
                else:
                    field_data = None

            data[field.name] = field_data

        if _extra_attrs:
            for attr_name in _extra_attrs:
                attr = getattr(self, attr_name)
                if callable_(attr):
                    data[attr_name] = attr()
                else:
                    data[attr_name] = attr

        if _backrefs and _recurse:
            for foreign_key, rel_model in self._meta.backrefs.items():
                if foreign_key.backref == "+":
                    continue
                descriptor = getattr(model_class, foreign_key.backref)
                if descriptor in _exclude or foreign_key in _exclude:
                    continue
                if only and (descriptor not in only) and (foreign_key not in only):
                    continue

                accum = []
                _exclude.add(foreign_key)
                related_query = getattr(self, foreign_key.backref)

                for rel_obj in related_query:
                    accum.append(
                        rel_obj.to_dict(
                            recurse=recurse,
                            backrefs=backrefs,
                            only=only,
                            exclude=exclude,
                            max_depth=max_depth - 1,
                        )
                    )

                data[foreign_key.backref] = accum

        return data


class Skill(BaseModel):
    _backrefs_ = False  # exclude exams, seekers and jobs

    title = CharField()
    desc = CharField(null=True)
    # exams
    # seekers
    # jobs


class Exam(BaseModel):
    _recurse_ = True
    _backrefs_ = True
    _exclude_ = ["skill"]

    title = CharField()
    skill = ForeignKeyField(Skill, backref="exams")
    # questions


class Question(BaseModel):
    _recurse_ = False
    _backrefs_ = True

    exam = ForeignKeyField(Exam, backref="questions")
    content = CharField()
    # answers


class Answer(BaseModel):
    _recurse_ = False
    _exclude_ = ["score"]

    question = ForeignKeyField(Question, backref="answers")
    content = CharField()
    score = FloatField(default=0)


class User(BaseModel):
    _exclude_ = ["pass_hash", "job_requests"]
    id = UUIDField(primary_key=True, default=uuid4)
    firstname = CharField(null=True)
    lastname = CharField(null=True)
    email = FixedCharField(64, index=True)
    phone_number = FixedCharField(9, index=True)
    pass_hash = CharField()
    # job_requests

    def verify_password(self, password):
        check_password_hash(self.pass_hash, password)

    def set_password(self, password):
        self.pass_hash = generate_password_hash(password)

    @staticmethod
    def hash_password(password):
        return generate_password_hash(password)


class Employer(User):
    co_name = TextField(null=True)
    co_address = TextField(null=True)
    co_phones = TextField(null=True)
    co_ver_code = TextField(null=True)
    # jobs


class Seeker(User):
    cv_content = TextField(null=True)
    # skills


class SkillSeeker(BaseModel):
    seeker = ForeignKeyField(Seeker, backref="skills")
    skill = ForeignKeyField(Skill, backref="seekers")
    score = IntegerField()


class Job(BaseModel):
    _exclude_ = ["requests"]
    title = TextField()
    content = TextField()
    min_salary = IntegerField()
    max_salary = IntegerField()
    created_on = DateTimeField(default=datetime.datetime.now)
    expire_on = DateTimeField()
    expired = BooleanField(False, default=False)
    employer = ForeignKeyField(Employer, backref="jobs")
    skills = ManyToManyField(Skill, backref="jobs")
    # requests

    @classmethod
    def get(cls, *query, **filters):
        res = super().get(*query, **filters)
        if res.expire_on <= datetime.datetime.now():
            res.expired = True

        return res


JobSkill = Job.skills.get_through_model()


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
    SkillSeeker,
    JobSkill,
    Seeker,
    Employer,
    Job,
)