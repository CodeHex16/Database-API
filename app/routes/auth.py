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


def get_user_repository(db: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Restituisce il repository della collection users.
    """
    return UserRepository(db)


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_user(
    user: schemas.UserAuth, user_repository=Depends(get_user_repository)
):
    """
    Inserisce un nuovo utente nella collection user.
    """
    # Verifica se l'utente esiste già
    db_user = await user_repository.get_by_email(user.email)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )

    # Crea un nuovo utente
    hashed_password = get_password_hash(user.password)
    user_data = schemas.User(
        email=user.email, hashed_password=hashed_password, is_initialized=False
    ).model_dump()

    await user_repository.create(user_data)
    return {"message": "User created successfully"}


async def authenticate_user(email: str, password: str, user_repo: UserRepository):
    """
    Ritorna true se l'utente esiste e se la password inserita è quella associata alla mail passata come parametro; altrimenti false.
    """
    # user_repo is now expected to be a valid UserRepository instance
    user = await user_repo.get_by_email(email)
    if not user:
        return False
    if not verify_password(password, user["hashed_password"]):
        return False
    return user


async def check_user_initialized(token: str, user_repo: UserRepository):
    """
    Ritorna il valore della flag _is_initialized_ dell'utente.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY_JWT, algorithms=[ALGORITHM])
        user_email = payload.get("sub")

        user = await user_repo.get_by_email(user_email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        return user["is_initialized"]
    except JWTError:
        raise HTTPException(
            status_code=403,
            detail="Token is invalid or expired during initialization check",
        )


def create_access_token(
    data: dict, scopes: List[str], expires_delta: Optional[timedelta] = None
):
    """
    Ritorna un token JWT di accesso appena creato.
    """
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
    """
    Se l'utente esiste ed ha inserito la password corretta crea e restituisce un token JWT di accesso che embedda email e permessi utente.
    """
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
        data={"sub": user["_id"]},
        scopes=user_permissions,
        expires_delta=access_token_expires,
    )
    return {"access_token": access_token, "token_type": "bearer"}


def verify_token(token: str, required_scopes: List[str] = None):
    """
    Verifica la validità del token JWT e restituisce il payload decodificato.
    """
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
async def verify_user_token(
    token: str, user_repository: UserRepository = Depends(get_user_repository)
):
    """
    Chiamata GET che verifica la validità del token JWT.
    """
    verify_token(token=token)

    is_initialized = await check_user_initialized(token, user_repository)

    if not is_initialized:
        return {
            "status": "not_initialized",
        }

    return {"status": "valid"}


def verify_user(token: str = Depends(oauth2_scheme)):
    """
    Verifica la validità del token JWT e restituisce il payload decodificato.
    """
    return verify_token(token)


def verify_admin(token: str = Depends(oauth2_scheme)):
    return verify_token(token, required_scopes=AccessRoles.ADMIN)


@router.get("/only_admin")
async def only_admin(
    current_user=Depends(verify_admin),
):
    """
    Endpoint accessibile solo agli amministratori.
    """
    return {
        "message": "Questo è un endpoint accessibile solo agli amministratori",
        "user": current_user.get("sub"),
    }
