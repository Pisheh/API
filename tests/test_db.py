import pytest
from peewee import Database, ManyToManyField
from app.models.dbmodel import *
from app.literals import CITIES
from random import randint, choices, choice
from datetime import timedelta
from datetime import datetime
from os.path import exists
from os import remove
from pprint import pprint
from slugify import slugify
from tests.data import *


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


employers = [
    {"name": "رایان آسان", "city": "تهران"},
    {"name": "نوآوران پارسیان", "city": "تهران"},
    {"name": "هوشمند پارسیان", "city": "تهران"},
    {"name": "آسان رایانه", "city": "تهران"},
    {"name": "فناوری اطلاعات باران", "city": "تهران"},
    {"name": "آواتک", "city": "تهران"},
    {"name": "فناوری اطلاعات ایرانسل", "city": "تهران"},
    {"name": "پارس سیستم", "city": "تهران"},
    {"name": "آی تی شرق", "city": "تهران"},
    {"name": "آریانتکنولوژی", "city": "تهران"},
    {"name": "پردازشگرا", "city": "تهران"},
    {"name": "پارس پاسارگاد", "city": "تهران"},
    {"name": "راهبرد", "city": "تهران"},
    {"name": "مدرن توسعه پارسیان", "city": "تهران"},
    {"name": "پیشتازان آریا", "city": "تهران"},
    {"name": "هوشمند سازان ایرانیان", "city": "تهران"},
    {"name": "فناوری اطلاعات زرین", "city": "تهران"},
    {"name": "پارتیکا", "city": "تهران"},
    {"name": "فناوری اطلاعات و ارتباطات پیشگامان", "city": "تهران"},
    {"name": "آی تکنولوژی آینده", "city": "تهران"},
]


class TestAddData:
    @pytest.fixture(autouse=True)
    def db_(self, db):
        self.db = db

    @pytest.mark.run(order=0)
    def test_add_skills(self):
        for job in JOBS:
            skills = []
            for skill_title in job["skills"]:
                skill, c = Skill.get_or_create(
                    slug=slugify(skill_title), title=skill_title
                )
                skills.append(skill.slug)
            job["skills"] = skills

    def test_add_guides(self):
        for guide in GUIDES:
            Guide.create(**guide)

    @pytest.mark.run(order=2)
    def test_add_employer(self):
        for i, employer in enumerate(employers):
            user = User.create(
                email=f"example{i}@example.com",
                phone_number=f"091234567{i:02d}",
                pass_hash=User.hash_password(f"password{i}"),
                role="employer",
            )
            user.employer = Employer.create(
                co_name=employer["name"], city=choice(CITIES)
            )

    @pytest.mark.run(order=3)
    def test_add_categories(self):
        for category in JOB_CATEGORIES:
            JobCategory.create(**category)

    @pytest.mark.run(order=3)
    def test_add_job(self):
        emp = [e for e in Employer.select()]
        for i in range(123):
            job = JOBS[i % len(JOBS)]
            min_salary, max_salary = choices(
                ((0, 0), (randint(10, 30) * 100_000, randint(30, 70) * 100_000)),
                (3, 7),
                k=1,
            )[0]
            j = Job.create(
                title=job["title"],
                description=job["description"],
                requirements=job["requirements"],
                expire_on=datetime(2025, 2, 3),
                created_on=datetime.now()
                - timedelta(
                    i * randint(0, 10) / 10,
                    i * (10, 30, 60, 120, 600, 3600)[i % 6],
                ),
                employer=emp[i % len(emp)],
                min_salary=min_salary,
                max_salary=max_salary,
                category=JobCategory.get_or_none(
                    JobCategory.slug == job["job_category"]["slug"]
                ),
            )
            for skill in job["skills"]:
                j.skills.add(Skill.get_by_id(skill))
            j.save()
