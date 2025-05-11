import os
from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime, timedelta, timezone
from app.utils import get_timezone
from fastapi.security import (
    OAuth2PasswordBearer,
    OAuth2PasswordRequestForm,
)
from passlib.context import CryptContext
from jose import JWTError, jwt
from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from dotenv import load_dotenv


from app.repositories.user_repository import UserRepository, get_user_repository
import app.schemas as schemas
from app.utils import verify_password
from app.service.auth_service import AccessRoles

load_dotenv()

SECRET_KEY_JWT = os.getenv("SECRET_KEY_JWT") or "$2b$12$zqt9Rgv1PzORjG5ghJSb6OSdYrt7f7cLc38a21DgX/DMyqt80AUCi"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES") or 60 * 24 * 30

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def security_check(): # pragma: no cover
    if SECRET_KEY_JWT == "$2b$12$zqt9Rgv1PzORjG5ghJSb6OSdYrt7f7cLc38a21DgX/DMyqt80AUCi":
        print(
            "WARNING: SECRET_KEY_JWT is not set. Using default value for development purposes only."
        )
        print("Please set SECRET_KEY_JWT in your environment variables.")
security_check()


async def authenticate_user(email: str, password: str, user_repo: UserRepository):
    """
    Ritorna true se l'utente esiste e se la password inserita è quella associata alla mail passata come parametro; altrimenti false.
    """
    user = await user_repo.get_by_email(email)
    if not user:
        return False
    hashed_pwd_from_db = user.get("hashed_password")
    if not hashed_pwd_from_db or not verify_password(password, hashed_pwd_from_db):
        return False
    return user


async def check_user_initialized(token: str, user_repo: UserRepository):
    """
    Ritorna il valore della flag _is_initialized_ dell'utente.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY_JWT, algorithms=[ALGORITHM])
        user_email = payload.get("sub")
        if not user_email:
            raise HTTPException(status_code=403, detail="User not exists")

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
        expire = datetime.now(get_timezone()) + expires_delta
    else:
        expire = datetime.now(get_timezone()) + timedelta(minutes=60 * 24)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY_JWT, algorithm=ALGORITHM)
    return encoded_jwt


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


def verify_user(token: str = Depends(oauth2_scheme)):
    """
    Verifica la validità del token JWT e restituisce il payload decodificato.
    """
    return verify_token(token)


def verify_admin(token: str = Depends(oauth2_scheme)):
    """
    Verifica la validità del token JWT e restituisce il payload decodificato.
    """
    return verify_token(token, required_scopes=AccessRoles.ADMIN)


@router.post("/token", response_model=schemas.Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    remember_me: bool = False,
    user_repository=Depends(get_user_repository),
):
    """
    Generazione del token JWT per l'autenticazione dell'utente.

    ### Pre-requisiti:
    * L'utente deve esistere e inserire la password corretta.

    ### Args:
    * **form_data**: Dati del modulo di accesso dell'utente.
        * **username**: Email dell'utente.
        * **password**: Password dell'utente.
    * **remember_me**: Flag per la durata del token; se True scade dopo 30 giorni, altrimenti fino alla chiusura del browser.

    ### Returns:
    * **access_token**: Token JWT generato.
    * **token_type**: Tipo di token (Bearer).

    ### Raises:
    * **HTTPException.HTTP_401_UNAUTHORIZED**: Se non vengono fornite credenziali valide.
    """
    # Verifica le credenziali dell'utente
    user = await user_repository.get_by_email(form_data.username)
    if not user or not verify_password(form_data.password, user.get("hashed_password")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Ottieni i permessi dell'utente
    user_permissions = user.get("scopes", ["user"])

    if user.get("remember_me") != remember_me:
        # Aggiorna il flag remember_me dell'utente
        await user_repository.update_user(
            user_id=user.get("_id"),
            user_data=schemas.UserUpdate(
                _id=user.get("_id"),
                remember_me=remember_me,
            ),
        )

    # Crea il token di accesso
    if remember_me:
        access_token_expires = timedelta(minutes=int(ACCESS_TOKEN_EXPIRE_MINUTES))
        expires_in = int(ACCESS_TOKEN_EXPIRE_MINUTES) * 60
    else:
        # se access_token_expires è None, il token dura 24 ore ma il cookie che lo contiene scade alla chiusura del browser
        access_token_expires = None
        expires_in = None
    access_token = create_access_token(
        data={"sub": user.get("_id")},
        scopes=user_permissions,
        expires_delta=access_token_expires,
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": expires_in,
    }


@router.get("/verify")
async def verify_user_token(
    token: str, user_repository: UserRepository = Depends(get_user_repository)
):
    """
    Verifica la validità del token JWT e restituisce il payload decodificato.
    ### Args:
    * **token**: Token JWT da verificare.

    ### Returns:
    * **status**: Stato del token (valid/not_initialized).
    * **scopes**: Permessi dell'utente associato al token.

    ### Raises:
    * **HTTPException.HTTP_403_FORBIDDEN**: Se il token non è valido o è scaduto.
    """
    payload = verify_token(token=token)

    is_initialized = await check_user_initialized(token, user_repository)

    if not is_initialized:
        return {
            "status": "not_initialized",
        }

    return {"status": "valid", "scopes": payload.get("scopes")}
