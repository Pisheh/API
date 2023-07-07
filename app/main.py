from fastapi import FastAPI, status, Request, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from fastapi.security import OAuth2PasswordRequestForm
from fastapi_utils.tasks import repeat_every
import uvicorn
from peewee import SqliteDatabase, IntegrityError, DoesNotExist
from datetime import datetime, timedelta
from logging import getLogger
from typing import Annotated
from app.routers import (
    guidance,
    jobs,
    me,
    literals,
    category,
    courses,
    users,
    jobrequest,
)
from app.models.schemas import (
    Username,
    UserQuery,
    UserQueryResult,
    UserSchema,
    LoginInfo,
    LoginResult,
    SignupInfo,
    SudoToken,
)
from app.models.dbmodel import (
    Seeker,
    Employer,
    User,
    Role,
    Job,
    database_proxy,
    JobRequest,
)
from app.utils import create_access_token, create_refresh_token, create_sudo_token
from app.deps import decode_refresh_token
from pydantic import BaseModel
import redis.asyncio as redis

from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter

app = FastAPI()
app.include_router(me.router, prefix="/me", tags=["User profile"])
app.include_router(guidance.router, prefix="/guidances", tags=["Guidance"])
app.include_router(jobs.router, prefix="/jobs", tags=["Jobs"])
app.include_router(category.router, prefix="/category", tags=["JobCategory"])
app.include_router(literals.router, prefix="/literals", tags=["Literals"])
app.include_router(courses.router, prefix="/courses", tags=["Courses"])
app.include_router(users.router, prefix="/users", tags=["Other users info"])
app.include_router(jobrequest.router, prefix="/requests", tags=["Job Request"])

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
    r = redis.from_url("redis://localhost", encoding="utf-8", decode_responses=True)
    await FastAPILimiter.init(r)
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


async def expire_jobs():
    for job in Job.select().where(Job.expire_on <= datetime.now()):
        job.expired = True
        job.save()


async def expire_job_requests():
    for jr in JobRequest.select().where(JobRequest.expire_on <= datetime.now()):
        jr.expired = True
        jr.save()


@app.on_event("startup")
@repeat_every(seconds=2 * 3600)  # 2hours
async def cron_jobs():
    await expire_jobs()


async def get_user(username) -> User:
    try:
        result: User
        email_match = Username.email_pattern.fullmatch(username)
        phone_match = Username.phone_pattern.fullmatch(username)
        if email_match:
            result = User.get(User.email == username)
        elif phone_match:
            result = User.get(User.phone_number == phone_match[1])
        else:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST, "send email or phone number"
            )

        if result.disabled:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "user.disabled")

        return result
    except DoesNotExist:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "user.not_found")


@app.post("/user")
async def check_user(login_info: UserQuery) -> UserQueryResult:
    result = await get_user(login_info.username)
    if result.role == Role.employer:
        return UserQueryResult(co_name=result.employer.co_name, role=Role.employer)
    elif result.role == Role.seeker:
        return UserQueryResult(
            firstname=result.seeker.firstname,
            lastname=result.seeker.lastname,
            role=Role.seeker,
        )


@app.post("/login", dependencies=[Depends(RateLimiter(times=2, seconds=3))])
async def login(
    login_info: Annotated[OAuth2PasswordRequestForm, Depends()]
) -> LoginResult:
    user = await get_user(login_info.username)

    if user and user.verify_password(login_info.password):
        return LoginResult(
            access_token=create_access_token(user),
            refresh_token=create_refresh_token(user),
            sudo_token=create_sudo_token(user),
            user_info=UserQueryResult(
                firstname=user.seeker.firstname if user.role == Role.seeker else None,
                lastname=user.seeker.lastname if user.role == Role.seeker else None,
                co_name=user.employer.co_name if user.role == Role.employer else None,
                role=user.role,
            ),
        )
    raise HTTPException(status.HTTP_401_UNAUTHORIZED, "login.incorrect_password")


@app.post("/sudo", dependencies=[Depends(RateLimiter(times=2, seconds=3))])
async def get_sudo_token(
    login_info: Annotated[OAuth2PasswordRequestForm, Depends()]
) -> SudoToken:
    user = await get_user(login_info.username)

    if user and user.verify_password(login_info.password):
        return SudoToken(sudo_token=create_sudo_token(user))
    raise HTTPException(status.HTTP_401_UNAUTHORIZED, "login.incorrect_password")


@app.post("/token")
async def refresh_token(user: Annotated[User, Depends(decode_refresh_token)]):
    return LoginResult(
        access_token=create_access_token(user),
        refresh_token=create_refresh_token(user),
        user_info=UserQueryResult(
            firstname=user.seeker.firstname if user.role == Role.seeker else None,
            lastname=user.seeker.firstname if user.role == Role.seeker else None,
            co_name=user.employer.co_name if user.role == Role.employer else None,
            role=user.role,
        ),
    )


@app.post("/signup", dependencies=[Depends(RateLimiter(times=2, seconds=5))])
async def signup(signup_info: SignupInfo) -> UserSchema:
    if not (signup_info.employer or signup_info.seeker):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "SignupInfo.employer or SignupInfo.seeker missed",
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


if __name__ == "__main__":
    uvicorn.run(app)
