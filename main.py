from typing import Union, Optional
from typing_extensions import Annotated
from fastapi import FastAPI, Depends, HTTPException, status
from datetime import datetime, timedelta, timezone
from pydantic import BaseModel, EmailStr, Field
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
import os
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

from contextlib import asynccontextmanager
from logging import info
from jose import JWTError, jwt


import schemas

load_dotenv()

MONGODB_URL = os.getenv("MONGODB_URL")


async def lifespan(app: FastAPI):
    # Startup
    app.mongodb_client = AsyncIOMotorClient(os.environ["MONGODB_URL"])
    app.database = app.mongodb_client.get_default_database()

    yield

    # Shutdown
    app.mongodb_client.close()


app = FastAPI(
    lifespan=lifespan,
    title="Suppl-AI MongoDB API",
    description="This is the API for the Suppl-AI MongoDB project",
    version="0.1",
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

origins = ["http://localhost:3000", "http://localhost:8000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def get_user_by_email(email: EmailStr):
    return await app.database.get_collection("users").find_one({"email": email})


@app.post("/register")
async def register_user(user: schemas.UserRegister):
    # Check if user already exists
    if await get_user_by_email(user.email):
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = pwd_context.hash(user.password)
    db_user = schemas.UserDB(
        email=user.email, hashed_password=hashed_password, is_initialized=False
    )

    await app.database.get_collection("users").insert_one(db_user.model_dump())
    return "User created successfully"


# ----------------- AUTHENTICATION -----------------
SECRET_KEY = "your_secret_key"  # da cambiare
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


# Authenticate the user
async def authenticate_user(email: str, password: str):
    user = await get_user_by_email(email)
    if not user:
        return False
    if not pwd_context.verify(password, user["hashed_password"]):
        return False
    return user


# Create access token
def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


@app.post("/token")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> schemas.Token:
    # usare username al posto di email
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["email"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


def verify_token(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=403, detail="Token is invalid or expired")
        return payload
    except JWTError:
        raise HTTPException(status_code=403, detail="Token is invalid or expired")


@app.get("/verify-token/{token}")
async def verify_user_token(token: str):
    verify_token(token=token)
    return {"message": "Token is valid"}


@app.get("/items/")
async def read_items(token: Annotated[str, Depends(oauth2_scheme)]):
    return {"token": token}
