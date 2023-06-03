import pytest
from peewee import Database, ManyToManyField
from dbmodel import *
from random import randint, choices, choice
from datetime import timedelta
from datetime import datetime
from os.path import exists
from os import remove


@pytest.fixture(scope="session", autouse=True)
def rm_db():
    if exists(".testdb.sqlite"):
        remove(".testdb.sqlite")


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
    def db_(self, db):
        self.db = db

    @pytest.mark.order("first")
    def test_add_skills(self):
        skills = [
            {"title": "python"},
            {"title": "php"},
            {"title": "react"},
            {"title": "مکانیک"},
            {"title": ".net"},
            {"title": "ASP"},
        ]

        for skill in skills:
            skill = Skill(**skill)
            res = skill.save()
            assert res, f"skill.save() returned {res}"

    @pytest.mark.order("second")
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
            exam = Exam(**exam)
            exam.save()

        for question in questions:
            q = Question(**question)
            q.save()

        for answer in answers:
            ans = Answer(**answer)
            ans.save()

    @pytest.mark.order(3)
    def test_add_employer(self):
        employers = [
            dict(
                email="example@example.com",
                phone_number="09123456789",
                pass_hash=User.hash_password("password1"),
                co_name="آذر سیستم",
            ),
            dict(
                email="example2@example.com",
                phone_number="09987654321",
                pass_hash=User.hash_password("password2"),
                co_name="سوران",
            ),
            dict(
                email="example3@example.com",
                phone_number="09987654323",
                pass_hash=User.hash_password("password2"),
                co_name="سریع سیستم جنوب",
            ),
        ]

        for employer in employers:
            res = Employer(**employer).save()
            assert res, f"Employer.save() returned {res}"

    @pytest.mark.order(4)
    def test_add_job(self):
        jobs = [
            (
                "گرافیست",
                "به یک گرافیست ماهر برای طراحی لوگو نیازمند هستیم، جهت کار تمام وقت",
            ),
            ("نقشه کش", "به یک نقسه کش نیازمندیم"),
            (
                "برنامه نویس بک‌اند",
                "به یک برنامه نویس ماهر برای بک‌اند یک سایت نیازمندیم",
            ),
            (
                "برنامه‌نویس فرانت",
                "به یک برنامه‌نویس فرانت‌اند برای ساخت یک سایت کاریابی نیازمندیم",
            ),
            ("تدوینگر فیلم مجالس", "به یک تدیونگر ماهر و خوش سلیقه نیازمندیم"),
            ("عکاس حرفه‌ای", "به یک عکاس حرفه‌ای جهت کار در آتلیه نیازمندیم"),
        ]

        cities = ["بندرعباس", "تهران", "اصفهان", "یزد"]

        for i in range(12345):
            title, content = choice(jobs)

            j = Job.create(
                title=title,
                city=choice(cities),
                content=content,
                agreed_price=choice((True, False)),
                expire_on=datetime(2025, 2, 3),
                created_on=datetime.now()
                - timedelta(
                    i // randint(0, 10), i * (10, 30, 60, 120, 600, 3600)[i % 6]
                ),
                employer=randint(1, 2),
                min_salary=randint(10, 30) * 100_000,
                max_salary=randint(30, 70) * 100_000,
            )
            for i in set(choices(range(1, 7), k=randint(1, 6))):
                j.skills.add(Skill.get_by_id(i))
            j.save()
