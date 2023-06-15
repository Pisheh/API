import pytest
from peewee import Database, ManyToManyField
from app.models.dbmodel import *
from random import randint, choices, choice
from datetime import timedelta
from datetime import datetime
from os.path import exists
from os import remove
from pprint import pprint


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


jobs = [
    {
        "title": "توسعه‌دهنده وب",
        "desc": "طراحی و پیاده‌سازی وبسایت‌ها و برنامه‌های کاربردی وب",
        "req": ["مسلط به HTML, CSS, JavaScript"],
        "skills": ["React", "Vue", "Angular"],
    },
    {
        "title": "توسعه‌دهنده نرم‌افزار",
        "desc": "طراحی و توسعه نرم‌افزارهای رومیزی، سیستم‌های تحت شبکه و سرویس‌های وب",
        "req": ["مسلط به زبان‌های برنامه‌نویسی مانند Java, C#, Python"],
        "skills": ["OOP", "Design Patterns", "Database Management"],
    },
    {
        "title": "کارشناس تست نرم‌افزار",
        "desc": "بررسی و اطمینان از کیفیت و عملکرد صحیح نرم‌افزارها",
        "req": ["آشنایی با مفاهیم تست، نیازمندی‌ها و مستندات مرتبط"],
        "skills": ["Test Automation", "Selenium", "JUnit"],
    },
    {
        "title": "طراح گرافیک",
        "desc": "طراحی و ایجاد تصاویر و گرافیک‌های مورد نیاز در پروژه‌ها",
        "req": ["مسلط به نرم‌افزارهای طراحی مانند Adobe Photoshop, Illustrator"],
        "skills": ["UI/UX Design", "Typography", "Color Theory"],
    },
    {
        "title": "کارشناس فروش و بازاریابی",
        "desc": "ارائه محصولات و خدمات شرکت به مشتریان و ایجاد روابط تجاری",
        "req": ["مهارت‌های ارتباطی بالا و توانایی مذاکره"],
        "skills": ["CRM", "Digital Marketing", "Sales Management"],
    },
    {
        "title": "تحلیل‌گر داده",
        "desc": "بررسی داده‌ها و ارائه راهکارهای بهبود عملکرد شرکت",
        "req": ["آشنایی با زبان‌های برنامه‌نویسی مانند Python, R"],
        "skills": ["Data Visualization", "Machine Learning", "Statistics"],
    },
    {
        "title": "مهندس شبکه",
        "desc": "طراحی، نصب و راه‌اندازی و نگه‌داری سیستم‌های شبکه",
        "req": ["مسلط به مفاهیم شبکه‌های کامپیوتری و تجهیزات مرتبط"],
        "skills": ["Routing", "Switching", "Network Security"],
    },
    {
        "title": "کارشناس پشتیبانی نرم‌افزار",
        "desc": "پاسخ‌گویی به سوالات کاربران و رفع مشکلات نرم‌افزاری",
        "req": ["آشنایی با محصولات شرکت و مهارت‌های حل مسئله"],
        "skills": ["Customer Service", "Troubleshooting", "Technical Writing"],
    },
    {
        "title": "توسعه‌دهنده برنامه‌های موبایل",
        "desc": "طراحی و پیاده‌سازی برنامه‌های کاربردی موبایل برای سیستم‌عامل‌های مختلف",
        "req": ["مسلط به زبان‌های برنامه‌نویسی مانند Java, Swift, Kotlin"],
        "skills": ["Android", "iOS", "React Native"],
    },
    {
        "title": "کارشناس امنیت اطلاعات",
        "desc": "ارزیابی و بهبود امنیت سیستم‌های کامپیوتری و شبکه‌های اطلاعاتی",
        "req": ["آشنایی با مفاهیم امنیتی و تکنیک‌های مربوطه"],
        "skills": ["Penetration Testing", "Cryptography", "Security Policies"],
    },
    {
        "title": "مدیر پروژه",
        "desc": "برنامه‌ریزی، هدایت و کنترل تیم‌های پروژه برای تحقق اهداف مشخص‌شده",
        "req": ["مهارت‌های مدیریتی و ارتباطی بالا"],
        "skills": ["Agile", "Scrum", "Risk Management"],
    },
    {
        "title": "معمار معلوماتی",
        "desc": "طراحی و پیاده‌سازی ساختارهای داده و استانداردهای استفاده از آن‌ها",
        "req": ["آشنایی با مفاهیم معماری اطلاعات و سیستم‌های پایگاه داده"],
        "skills": ["Big Data", "Data Modeling", "Database Design"],
    },
    {
        "title": "مدیر بازاریابی",
        "desc": "برنامه‌ریزی و اجرای استراتژی‌های بازاریابی و تبلیغاتی برای یک شرکت",
        "req": ["تجربه در حوزه بازاریابی و مدیریت تیم‌های بازاریابی"],
        "skills": ["Marketing Strategy", "Brand Management", "Content Marketing"],
    },
    {
        "title": "مدیر مالی",
        "desc": "مسئولیت مدیریت مالی و بودجه‌بندی شرکت",
        "req": ["تجربه در حوزه مالی و مدیریت تیم‌های مالی"],
        "skills": ["Financial Analysis", "Budgeting", "Investment Management"],
    },
    {
        "title": "مهندس الکترونیک",
        "desc": "طراحی و ساخت مدارها و سیستم‌های الکترونیکی",
        "req": ["مسلط به مفاهیم و تکنیک‌های مهندسی الکترونیک"],
        "skills": ["PCB Design", "Embedded Systems", "Analog Circuit Design"],
    },
    {
        "title": "مهندس مکانیک",
        "desc": "طراحی و ساخت ماشین‌آلات و سیستم‌های مکانیکی",
        "req": ["مسلط به مفاهیم و تکنیک‌های مهندسی مکانیک"],
        "skills": ["CAD", "Finite Element Analysis", "Thermodynamics"],
    },
]

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

cities = [
    "تهران",
    "مشهد",
    "اصفهان",
    "کرج",
    "تبریز",
    "شیراز",
    "اهواز",
    "قم",
    "کرمانشاه",
    "رشت",
    "زاهدان",
    "کرمان",
    "ارومیه",
    "یزد",
    "سنندج",
    "همدان",
    "بندرعباس",
    "اردبیل",
    "ساری",
    "بجنورد",
]


class TestAddData:
    @pytest.fixture(autouse=True)
    def db_(self, db):
        self.db = db

    @pytest.mark.order("first")
    def test_add_skills(self):
        for job in jobs:
            skills = []
            for skill_title in job["skills"]:
                skill, c = Skill.get_or_create(title=skill_title)
                skills.append(skill.id)
            job["skills"] = skills

    @pytest.mark.order("second")
    def test_add_employer(self):
        for i, employer in enumerate(employers):
            res = Employer(
                email=f"example{i}@example.com",
                phone_number=f"0912345678{i}",
                pass_hash=User.hash_password(f"password{i}"),
                co_name=employer["name"],
                city=choice(cities)["name"],
            ).save()
            assert res, f"Employer.save() returned {res}"

    @pytest.mark.order(3)
    def test_add_job(self):
        for i in range(12345):
            job = jobs[i % len(jobs)]
            pprint(job)
            min_salary, max_salary = choices(
                ((0, 0), (randint(10, 30) * 100_000, randint(30, 70) * 100_000)),
                (3, 7),
                k=1,
            )[0]
            j = Job.create(
                title=job["title"],
                description=job["desc"],
                requirements=";".join(job["req"]),
                expire_on=datetime(2025, 2, 3),
                created_on=datetime.now()
                - timedelta(
                    i * randint(0, 10) / 10,
                    i * (10, 30, 60, 120, 600, 3600)[i % 6],
                ),
                employer=randint(1, len(employers)),
                min_salary=min_salary,
                max_salary=max_salary,
            )
            for skill in job["skills"]:
                j.skills.add(Skill.get_by_id(skill))
            j.save()
