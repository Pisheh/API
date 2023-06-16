from fastapi import FastAPI, status, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from fastapi_utils.tasks import repeat_every
import uvicorn
from peewee import SqliteDatabase, IntegrityError, DoesNotExist
from datetime import datetime, timedelta
from logging import getLogger

from app.routers import guidance, jobs, users, literals
from app.models.schemas import (
    UserQuery,
    UserQueryResult,
    UserSchema,
    LoginInfo,
    LoginResult,
    SignupInfo,
)
from app.models.dbmodel import Seeker, Employer, User, Role, Job, database_proxy
from app.utils import create_access_token

app = FastAPI()
app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(guidance.router, prefix="/guidances", tags=["Guidance"])
app.include_router(jobs.router, prefix="/jobs", tags=["Jobs"])
app.include_router(literals.router, prefix="/literals", tags=["Literals"])

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
    raise NotImplemented  # TODO: expire job reauests


@app.on_event("startup")
@repeat_every(seconds=2 * 3600)  # 2hours
async def cron_jobs():
    await expire_jobs()


@app.post("/user")
async def get_user(user: UserQuery) -> UserQueryResult:
    try:
        result: User = None
        if user.email:
            result = User.get(User.email == user.email)
        elif user.number:
            result = User.get(User.number == user.number)
        else:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST, "send email or phone number"
            )

        if result.disabled:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "user.disabled")

        return result.to_schema(UserQueryResult)
    except DoesNotExist:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "user.not_found")


@app.post("/signup")
async def signup(signup_info: SignupInfo) -> UserSchema:
    if not (signup_info.employer or signup_info.seeker):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "SignupInfo.employer of SignupInfo.seeker missed",
        )
    try:
        user = User.create(
            pass_hash=User.hash_password(signup_info.password),
            **signup_info.dict(exclude={"employer", "seeker", "password"}),
        )
        if signup_info.role == Role.Employer:
            user.employer = Employer.create(**signup_info.employer.dict())
        elif signup_info.role == Role.seeker:
            user.seeker = Seeker.create(**signup_info.seeker.dict())
        user.save()
        return user.to_schema(UserSchema)
    except IntegrityError:
        raise HTTPException(status.HTTP_409_CONFLICT, "user.exists")


@app.post("/login")
async def login(login_info: LoginInfo) -> LoginResult:
    try:
        user: User
        if login_info.email:
            user = User.get(User.email == login_info.email)
        elif login_info.phone_number:
            user = User.get(User.phone_number == login_info.phone_number)

        if user and user.verify_password(login_info.password):
            return LoginResult(
                token=create_access_token(user), user_info=user.to_schema(UserSchema)
            )
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "login.incorrect_password")
    except DoesNotExist:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "user.not_found")


if __name__ == "__main__":
    uvicorn.run(app)
