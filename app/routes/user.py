import os
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from typing import List, Optional
from datetime import datetime
from pydantic import EmailStr
import requests
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo.errors import DuplicateKeyError
from jose import jwt, JWTError

from app.database import get_db
import app.schemas as schemas
from app.routes.auth import (
    verify_admin,
    verify_user,
    authenticate_user,
    get_user_repository,
)
from app.repositories.user_repository import UserRepository
from app.utils import get_password_hash, get_uuid3, verify_password

router = APIRouter(
    prefix="/user",
    tags=["user"],
)

SECRET_KEY_JWT = os.getenv("SECRET_KEY_JWT")
if not SECRET_KEY_JWT:
    raise ValueError("SECRET_KEY_JWT non impostata nelle variabili d'ambiente")

ALGORITHM = "HS256"


@router.get(
    "/",
    response_model=List[schemas.User],
    status_code=status.HTTP_200_OK,
)
async def get_users(
    current_user=Depends(verify_admin),
    user_repo: UserRepository = Depends(get_user_repository),
):
    """
    Restituisce una lista di tutti gli utenti registrati.
    """
    users = await user_repo.get_users()

    # Ritorna la lista di user se esistente, altrimeni solleva un'eccezione 404
    if not users:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No users found",
        )
    return users


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
)
async def register_user(
    user_email: EmailStr,
    current_user=Depends(verify_admin),
    user_repo: UserRepository = Depends(get_user_repository),
):
    """
    Crea un nuovo utente con una password temporanea casuale.
    L'utente riceverà un'email con la password temporanea.
    """
    # Genera una password temporanea casuale
    password = os.urandom(16).hex()
    # print(f"Generated password: {password}")

    hashed_password = get_password_hash(password)
    new_user = {
        # "_id": get_uuid3(user_email),
        "_id": user_email,
        "hashed_password": hashed_password,
        "is_initialized": False,
        "remember_me": False,
        "scopes": ["user"],
    }

    try:
        await user_repo.create_user(user_data=new_user)
    except DuplicateKeyError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {e}",
        )

    # Invia un'email all'utente con la password temporanea

    return {"message": "User registered successfully", "password": password}


@router.delete(
    "/delete",
    status_code=status.HTTP_200_OK,
)
async def delete_user(
    user_to_be_deleted: EmailStr,
    admin: schemas.UserAuth,
    current_user=Depends(verify_admin),
    user_repository: UserRepository = Depends(get_user_repository),
):
    """
    Elimina un utente esistente se la password inserita dall'admin è corretta.
    """
    # Verifica che l'utente esista e che la password sia corretta
    valid_user = await authenticate_user(admin.email, admin.password, user_repository)
    if not valid_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    if valid_user.get("_id") != current_user.get("sub"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Credentials do not match the logged-in admin",
        )

    # Elimina l'utente dal database using the injected repository
    try:
        result = await user_repository.collection.delete_one(
            {"_id": user_to_be_deleted}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete user: {e}",
        )

    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return {"message": "User deleted successfully"}


@router.put(
    "/edit",
    status_code=status.HTTP_200_OK,
)
async def edit_user(
    user_new_data: schemas.UserUpdate,
    current_user=Depends(verify_admin),
    user_repo: UserRepository = Depends(get_user_repository),
):
    """
    Modifica i dati di un utente esistente.
    La modifica può includere la password, lo stato di inizializzazione,
    la flag _remember_me_ e gli scopes. L'email (_id) non può essere modificata.
    Se per uno dei campi viene fornito è None (null nel body json della richiesta),
    il valore attuale rimarrà invariato.
    """
    # Ottiene i dati attuali dell'user
    user_current_data = await user_repo.get_by_email(user_new_data.id)

    # Verifica se l'utente esiste
    if not user_current_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Prepara il payload per l'aggiornamento
    update_payload = {
        # Hashing della password solo se non è None o stringa vuota
        "hashed_password": (
            get_password_hash(user_new_data.hashed_password)
            if user_new_data.hashed_password
            else user_current_data.get("hashed_password")
        ),
        "is_initialized": (
            user_new_data.is_initialized
            if user_new_data.is_initialized is not None
            else user_current_data.get("is_initialized")
        ),
        "remember_me": (
            user_new_data.remember_me
            if user_new_data.remember_me is not None
            else user_current_data.get("remember_me")
        ),
        "scopes": (
            user_new_data.scopes
            if user_new_data.scopes is not None
            else user_current_data.get("scopes")
        ),
    }

    # Aggiorna i dati dell'utente nel database
    try:
        result = await user_repo.collection.update_one(
            {"_id": user_new_data.id},
            {"$set": update_payload},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user: {e}",
        )

    # Controlla se l'aggiornamento ha avuto effetto
    if result.modified_count == 0 and result.matched_count > 0:
        return {"message": "User data is already up to date."}
    elif result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found during update attempt",
        )

    return {"message": "User updated successfully"}


@router.put(
    "/update_password",
    status_code=status.HTTP_200_OK,
)
async def update_password(
    user: schemas.UserUpdatePassword,
    user_repository: UserRepository = Depends(get_user_repository),
):
    """
    Aggiorna la password dell'utente.
    """

    # Verfifica se l'utente esiste e se la password è corretta
    try:
        await authenticate_user(user.email, user.current_password, user_repository)
    except Exception as e:
        print(f"Error authenticating user: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    # Aggiorna la password dell'utente
    try:
        hashed_password = get_password_hash(user.password)
        result = await user_repository.collection.update_one(
            {"_id": user.email},
            {"$set": {"hashed_password": hashed_password, "is_initialized": True}},
        )
    except Exception as e:
        print(f"Error updating password: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update password: {e}",
        )

    # Controlla se l'aggiornamento ha avuto effetto
    if result.modified_count == 0 and result.matched_count > 0:
        return {
            "message": "Password update did not modify the document (maybe same password?)."
        }
    elif result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found during password update attempt",
        )

    return {"message": "Password updated successfully"}
