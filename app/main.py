from fastapi import FastAPI, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from fastapi_utils.tasks import repeat_every
import uvicorn
from peewee import SqliteDatabase
from .models.dbmodel import Job, database_proxy
from datetime import datetime, timedelta
from math import ceil
from typing import Annotated
from logging import getLogger

from .routers import users, guidance, jobs

app = FastAPI()
app.include_router(users.router, tags=["Users"])
app.include_router(guidance.router, prefix="/guidances", tags=["Guidance"])
app.include_router(jobs.router, prefix="/jobs", tags="Jobs")

db_ = SqliteDatabase(".testdb.sqlite")
database_proxy.initialize(db_)


logger = getLogger("API")


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    exc_str = f"{exc}".replace("\n", " ").replace("   ", " ")
    # or logger.error(f'{exc}')
    logger.error(f"{exc_str}\n{exc.body}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder(
            {
                "description": exc_str,
                "detail": exc.errors(),
                "request": {
                    "method": request.method,
                    "headers": request.headers,
                    "body": exc.body,
                },
            }
        ),
    )


@app.on_event("startup")
async def startup():
    db_.connect()


@app.on_event("shutdown")
async def shutdown():
    db_.close()


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://pisheh.local:3000",
        "https://pisheh.netlify.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


expire_check = None


async def expire_jobs():
    global expire_check
    if (not expire_check) or datetime.now() - expire_check >= timedelta(hours=2):
        for job in Job.select():
            job.expire = job.expire_on <= datetime.now()
        expire_check = datetime.now()


async def expire_job_requests():
    ...  # TODO: expire job reauests


@app.on_event("startup")
@repeat_every(seconds=2 * 3600)  # 2hours
async def cron_jobs():
    await expire_jobs()


schedule.every(2).hours.do(cron_jobs)

if __name__ == "__main__":
    uvicorn.run(app)
