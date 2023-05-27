from mongoengine import *
from werkzeug.security import generate_password_hash, check_password_hash
from enum import Enum


class Answer(EmbeddedDocument):
    content = StringField()
    score = IntField()


class Question(EmbeddedDocument):
    question = StringField()
    answers = EmbeddedDocumentListField(Answer)


class Exam(Document):
    id = ObjectIdField(primary_key=True)
    questions = EmbeddedDocumentListField(Question)
    questions_count = IntField()


class Skill(Document):
    id = ObjectIdField(primary_key=True)
    title = StringField()
    desc = StringField()
    exams = ListField(ReferenceField(Exam))  # Many to Many


class Role(Enum):
    SEEKER = 1
    EMPLOYER = 2


class User(Document):
    id = ObjectIdField(primary_key=True)
    email = EmailField(index=True, unique=True)
    password_hash = StringField()
    role = EnumField(Role)
    extra_info = GenericLazyReferenceField()

    def verify_password(self, password):
        check_password_hash(self.password_hash, password)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)


class EmployerInfo(Document):
    id = ObjectIdField(primary_key=True)
    firstname = StringField()
    lastname = StringField()
    co_name = StringField()
    co_address = StringField()
    co_phones = ListField(StringField())
    co_ver_code = StringField()
    jobs = ListField(LazyReferenceField())


class SeekerInfo(Document):
    id = ObjectIdField(primary_key=True)
    firstname = StringField()
    lastname = StringField()
    phone_number = StringField(r"09\d{9}")
    cv = EmbeddedDocumentField("CV")


class CV(EmbeddedDocument):
    content = StringField()
    skills = ListField(ReferenceField(Skill))
    scores = ListField(IntField)


class job(Document):
    id = ObjectIdField(primary_key=True)
    title = StringField()
    content = StringField()
    skills = ListField(LazyReferenceField(Skill))
    min_salary = IntField()
    max_salary = IntField()
    expire = DateTimeField()
