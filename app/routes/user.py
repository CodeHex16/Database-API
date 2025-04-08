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
from app.routes.auth import verify_admin, verify_user
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
    print(f"Generated password: {password}")
    hashed_password = get_password_hash(password)
    new_user = {
        "_id": get_uuid3(user_email),
        "email": user_email,
        "hashed_password": hashed_password,
        "is_initialized": False,
        "scopes": ["user"],
    }

    # Create a user repository and get the database
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
