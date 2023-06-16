from dbmodel import *
from peewee import *
from schemas import *
from pprint import pprint
from datetime import timedelta

db_ = SqliteDatabase(".testdb.sqlite")
database_proxy.initialize(db_)
db_.connect()
db_.create_tables(TABLES)
jobs = []
for job in (
    Job.select().where(Job.expired == False).order_by(-Job.created_on).paginate(1, 10)
):
    job: Job
    pprint(job.to_schema(JobSchema).dict())

pprint(jobs)
db_.close()
