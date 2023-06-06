from fastapi import FastAPI, HTTPException, status, Request, Path
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
import uvicorn
from peewee import SqliteDatabase
from dbmodel import Seeker, Employer, User, Job, database_proxy
from peewee import IntegrityError
from deps import auth
from schemas import (
    AuthenticationInfo,
    AuthenticationResponse,
    NewUser,
    LoginResult,
    LoginInfo,
    Jobs,
    JobSchema,
    PageRequest,
    PaginationMeta,
)
from utils import generate_tokens
from datetime import datetime, timedelta
from math import ceil
from typing import Annotated
from logging import getLogger

app = FastAPI()
db_ = SqliteDatabase(".testdb.sqlite")
database_proxy.initialize(db_)


logger = getLogger("API")


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    exc_str = f"{exc}".replace("\n", " ").replace("   ", " ")
    # or logger.error(f'{exc}')
    logger.error(f"{exc_str}\n{exc.body}")
    content = {"message": exc_str}
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


async def cron_jobs():
    expire_jobs()


@app.middleware("http")
async def do_cron(request: Request, call_next):
    return await call_next(request)


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


@app.post("/user")
async def get_user(user: AuthenticationInfo) -> AuthenticationResponse:
    if user.email:
        if (seeker := Seeker.get_or_none(email=user.email)) is not None:
            return AuthenticationResponse(firstname=seeker.firstname, role="seeker")
        elif (employer := Employer.get_or_none(email=user.email)) is not None:
            return AuthenticationResponse(co_name=employer.co_name, role="employer")
        else:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "user.notfound")
    elif user.number:
        if (seeker := Seeker.get_or_none(phone_number=user.number)) is not None:
            return AuthenticationResponse(firstname=seeker.firstname, role="seeker")
        elif (employer := Employer.get_or_none(phone_number=user.number)) is not None:
            return AuthenticationResponse(co_name=employer.co_name, role="employer")
        else:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "user.notfound")


@app.post("/signup")
async def signup(user: NewUser):
    try:
        if user.role == "seeker":
            Seeker.create(
                pass_hash=Seeker.hash_password(user.password),
                **user.dict(exclude={"role", "password"}),
            )
            return dict(done=True)
        elif user.role == "employer":
            Employer.create(
                pass_hash=Seeker.hash_password(user.password),
                **user.dict(exclude={"role", "password"}),
            )
    except IntegrityError:
        raise HTTPException(status.HTTP_409_CONFLICT, "user.exists")


def verify_pass(user: User, password):
    if user and user.verify_password(password):
        return LoginResult(**generate_tokens(user))
    raise HTTPException(status.HTTP_401_UNAUTHORIZED, "login.incorrect_password")


@app.post("/login")
async def login(user: LoginInfo) -> LoginResult:
    db = None
    if user.role == "employer":
        db = Employer
    elif user.role == "seeker":
        db = Seeker

    if user.email:
        filters = {"email": user.email}
    elif user.number:
        filters = {"number": user.number}
    else:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "login.no_login_info")
    return verify_pass(db.get_or_none(**filters), user.password)


expire_check = None


def expire_jobs():
    global expire_check
    if not expire_check or datetime.now() - expire_check > timedelta(hours=2):
        for job in Job.select():
            job.expire = job.expire_on <= datetime.now()
        expire_check = datetime.now()


@app.post("/jobs/page")
async def get_jobs(page: PageRequest) -> Jobs:
    jobs_count = Job.select(Job.expired == False).count()
    pages_count = ceil(jobs_count / page.per_page)
    if page.page <= pages_count:
        jobs: list[JobSchema] = []
        for job in (
            Job.select()
            .where(Job.expired == False)
            .order_by(-Job.created_on)
            .paginate(page.page, page.per_page)
        ):
            jobs.append(job.to_schema(JobSchema))
        return Jobs(
            meta=PaginationMeta(
                success=True,
                total_count=jobs_count,
                current_page=page.page,
                page_count=pages_count,
                per_page=page.per_page,
            ),
            jobs=jobs,
        )
    else:
        HTTPException(400, "jobs.bad_pagination")


@app.get("/jobs/{job_id}")
async def get_jobs(
    job_id: Annotated[int, Path(title="The ID of the job to get", ge=1)]
) -> JobSchema:
    if (job := Job.get_or_none(job_id)) is not None and not job.expired:
        return job.to_schema(JobSchema)
    raise HTTPException(status.HTTP_404_NOT_FOUND, "job.not_found")


@app.get("/cron")
async def cron():
    cron_jobs()


if __name__ == "__main__":
    uvicorn.run(app)
