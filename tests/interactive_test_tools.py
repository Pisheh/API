from dbmodel import *
from peewee import *

db_ = SqliteDatabase(".testdb.sqlite")
database_proxy.initialize(db_)
db_.connect()
db_.create_tables(TABLES)
