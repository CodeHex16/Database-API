import os
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from typing import List, Optional
from datetime import datetime
from pydantic import EmailStr
import requests
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo.errors import DuplicateKeyError

from app.database import get_db
import app.schemas as schemas
from app.routes.auth import verify_admin, verify_user, authenticate_user
from app.repositories.user_repository import UserRepository
from app.utils import get_password_hash, get_uuid3

router = APIRouter(
    prefix="/user",
    tags=["user"],
)


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
)
async def register_user(user_email: EmailStr, current_user=Depends(verify_admin)):
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

    # Crea un'istanza del repository utente e ottiene il database
    user_repo = UserRepository(await get_db())
    try:
        await user_repo.create(user_data=new_user)
    except DuplicateKeyError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists",
        )

    # Invia un'email all'utente con la password temporanea

    return {"message": "User registered successfully", "password": password}


@router.delete(
    "/delete",
    status_code=status.HTTP_200_OK,
)
async def delete_user(
    user_to_be_deleted: EmailStr,
    admin: schemas.UserEmailPwd,
    current_user=Depends(verify_admin),
):
    """
    Elimina un utente esistente se la password inserita dall'admin è corretta.
    """
    # Crea un'istanza del repository utente e ottiene il database
    user_repo = UserRepository(await get_db())

    # Verifica che l'utente esista e che la password sia corretta
    valid_credentials = await authenticate_user(admin.email, admin.password, user_repo)
    if not valid_credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    # Elimina l'utente dal database
    result = await user_repo.collection.delete_one({"_id": user_to_be_deleted})

    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return {"message": "User deleted successfully"}


@router.post(
    "/edit",
    status_code=status.HTTP_200_OK,
)
async def edit_user(
    user_new_data: schemas.UserDB,
    current_user=Depends(verify_admin),
):
    """
    Modifica i dati di un utente esistente. La modifca può includere la password, lo stato di inizializzazione,
    la flag _remember_me_ e gli scopes, l'email, che è anche id dello user, non può essere modificata.
    """
    # Crea un'istanza del repository utente e ottiene il database
    user_repo = UserRepository(await get_db())

    # Aggiorna i dati dell'utente nel database
    result = await user_repo.collection.update_one(
        {"_id": user_new_data.id},
        {
            "$set": {
                "hashed_password": user_new_data.hashed_password,
                "is_initialized": user_new_data.is_initialized,
                "remember_me": user_new_data.remember_me,
                "scopes": user_new_data.scopes,
            }
        },
    )

    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return {"message": "User updated successfully"}
