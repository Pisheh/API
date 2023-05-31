import pytest
from peewee import Database
from dbmodel import *
from random import randint


@pytest.fixture()
def db():
    db_ = SqliteDatabase(".testdb.sqlite")
    database_proxy.initialize(db_)
    db_.connect()
    db_.create_tables(TABLES)
    yield db_
    db_.close()


class TestAddData:
    @pytest.fixture(autouse=True)
    def _connect_to_db(self, db):
        self.db = db

    def test_add_skills(self):
        skills = [{"title": "python"}, {"title": "php"}, {"title": "react"}]

        for skill in skills:
            skill = Skill.create(**skill)
            skill.save()

    def test_add_exams(self):
        exams = [
            {"title": f"exam {n}", "skill": s} for n in range(3) for s in range(1, 4)
        ]

        questions = [
            {"content": f"q{q}", "exam": ex} for q in range(1, 11) for ex in range(1, 4)
        ]

        answers = [
            {"content": f"ans {a}", "score": randint(0, 5), "question": q}
            for a in range(1, randint(2, 6))
            for q in range(1, 31)
        ]

        for exam in exams:
            exam = Exam.create(**exam)
            exam.save()

        for question in questions:
            q = Question.create(**question)
            q.save()

        for answer in answers:
            ans = Answer.create(**answer)
            ans.save()

    def test_get_exams(self):
        ...
