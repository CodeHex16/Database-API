import os
from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime, timedelta, timezone
from fastapi.security import (
    OAuth2PasswordBearer,
    OAuth2PasswordRequestForm,
    SecurityScopes,
)
from passlib.context import CryptContext
from logging import info, debug, error
from jose import JWTError, jwt
from typing import List, Optional
import bcrypt
from motor.motor_asyncio import AsyncIOMotorDatabase
from dotenv import load_dotenv


from app.repositories.user_repository import UserRepository
from app.database import get_db
import app.schemas as schemas
from app.utils import get_password_hash, verify_password
from app.service.auth_service import AccessRoles

load_dotenv()

SECRET_KEY_JWT = os.getenv("SECRET_KEY_JWT")
if not SECRET_KEY_JWT:
    raise ValueError("SECRET_KEY_JWT non impostata nelle variabili d'ambiente")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24


router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def init_router(app_instance):
    yield


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


# Authenticate the user
async def authenticate_user(
    email: str, password: str, user_repo: UserRepository = Depends(get_user_repository)
):
    user = await user_repo.get_by_email(email)
    if not user:
        return False
    if not verify_password(password, user["hashed_password"]):
        return False
    return user


# Create access token
def create_access_token(
    data: dict, scopes: List[str], expires_delta: Optional[timedelta] = None
):
    to_encode = data.copy()
    to_encode.update({"scopes": scopes})
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY_JWT, algorithm=ALGORITHM)
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

    # Ottieni i permessi dell'utente
    user_permissions = user.get("scopes", ["user"])

    # Crea il token di accesso
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["email"]},
        scopes=user_permissions,
        expires_delta=access_token_expires,
    )
    return {"access_token": access_token, "token_type": "bearer"}


def verify_token(token: str, required_scopes: List[str] = None):
    try:
        payload = jwt.decode(token, SECRET_KEY_JWT, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=403, detail="Token is invalid or expired")

        if required_scopes:
            user_permissions = payload.get("scopes", [])
            print(f"User permissions: {user_permissions}")
            if not any(scope in user_permissions for scope in required_scopes):
                raise HTTPException(
                    status_code=403,
                    detail=f"Permesso negato. Richiesto ruolo {required_scopes}",
                )
        return payload
    except JWTError:
        raise HTTPException(status_code=403, detail="Token is invalid or expired")


@router.get("/verify")
async def verify_user_token(token: str):
    payload = verify_token(token=token)
    return {"status": "valid", "scopes": payload.get("scopes")}


def verify_user(token: str = Depends(oauth2_scheme)):
    return verify_token(token)


def verify_admin(token: str = Depends(oauth2_scheme)):
    return verify_token(token, required_scopes=AccessRoles.ADMIN)


@router.get("/only_admin")
async def only_admin(
    current_user = Depends(verify_admin),
):
    return {
        "message": "Questo è un endpoint accessibile solo agli amministratori",
        "user": current_user.get("sub"),
    }
