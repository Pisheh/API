from fastapi import FastAPI, HTTPException, status, Depends

from .dbmodel import Seeker, Employer, User
from peewee import IntegrityError
from .deps import auth
from .schemas import UserInfo, BasicUserInfo, NewUser, LoginResult, LoginInfo
from .utils import generate_tokens

app = FastAPI()


@app.get("/user")
async def get_user(user: UserInfo) -> BasicUserInfo:
    if user.email:
        if seeker := Seeker.get_or_none(email=user.email) is not None:
            return BasicUserInfo(firstname=seeker.firstname, role="seeker")
        elif employer := Employer.get_or_none(email=user.email) is not None:
            return BasicUserInfo(firstname=employer.firstname, role="employer")
        else:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "user.notfound")
    elif user.number:
        if seeker := Seeker.get_or_none(phone_number=user.number) is not None:
            return BasicUserInfo(firstname=seeker.firstname, role="seeker")
        elif employer := Employer.get_or_none(phone_number=user.number) is not None:
            return BasicUserInfo(firstname=employer.firstname, role="employer")
        else:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "user.notfound")


@app.post("/user")
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
    return verify_pass(db.get_or_none(**filters))
