from fastapi import FastAPI, APIRouter, Depends, HTTPException, status
from typing_extensions import Annotated
from datetime import datetime, timedelta, timezone
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
from logging import info, debug, error
from jose import JWTError, jwt
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
import os

from motor.motor_asyncio import AsyncIOMotorDatabase

from ..repositories.user_repository import UserRepository
from ..database import get_db
from .. import schemas


router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)


# Variabili globali per memorizzare l'app e altre risorse
app = None


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def init_router(app_instance):
    global app
    app = app_instance
    print("Auth router initialized with app:", app_instance)
    print("App in db:", app.database)


# Dipendenza per ottenere il repository utenti
def get_user_repository(db: AsyncIOMotorDatabase = Depends(get_db)):
    return UserRepository(db)


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_user(
    user: schemas.UserRegister, user_repository=Depends(get_user_repository)
):
    # Verifica se l'utente esiste già
    db_user = await user_repository.get_by_email(user.email)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )

    # Crea un nuovo utente
    hashed_password = get_password_hash(user.password)
    user_data = schemas.UserDB(
        email=user.email, hashed_password=hashed_password, is_initialized=False
    ).model_dump()

    await user_repository.create(user_data)
    return {"message": "User created successfully"}


# ----------------- AUTHENTICATION -----------------
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


# Authenticate the user
async def authenticate_user(
    email: str, password: str, user_repo: UserRepository = Depends(get_user_repository)
):
    user = await user_repo.get_by_email(email)
    if not user:
        return False
    if not pwd_context.verify(password, user["hashed_password"]):
        return False
    return user


# Create access token
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


@router.post("/token", response_model=schemas.Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    user_repository=Depends(get_user_repository),
):
    # Verifica le credenziali dell'utente
    user = await user_repository.get_by_email(form_data.username)
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Crea il token di accesso
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


@router.post("/verify")
async def verify_user_token(token: str):
    verify_token(token=token)
    return {"status": "valid"}


# Aggiungiamo le funzioni mancanti per la gestione delle password
def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)
