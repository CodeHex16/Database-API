import os
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from typing import List, Optional
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
from app.service.email_service import EmailService

router = APIRouter(
    prefix="/users",
    tags=["user"],
)

SECRET_KEY_JWT = os.getenv("SECRET_KEY_JWT")
if not SECRET_KEY_JWT:
    raise ValueError("SECRET_KEY_JWT non impostata nelle variabili d'ambiente")

ALGORITHM = "HS256"


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
)
async def register_user(
    user_data: schemas.UserCreate,
    current_user=Depends(verify_admin),
    user_repo: UserRepository = Depends(get_user_repository),
):
    """
    Crea un nuovo utente con una password temporanea casuale.
    L'utente riceverà un'email con la password temporanea.
    """
    # Genera una password temporanea casuale
    password = os.urandom(16).hex()

    hashed_password = get_password_hash(password)
    new_user = {
        "_id": user_data.email,
        "name": user_data.name,
        "hashed_password": hashed_password,
        "is_initialized": False,
        "remember_me": False,
        "scopes": user_data.scopes if user_data.scopes else ["user"],
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

    await EmailService().send_email(
        to=[user_data.email],
        subject=f"[Suppl-AI] Registrazione utente",
        body=f"Benvenuto in Suppl-AI!\nEcco la tua password temporanea\n\n{password}\n\n Accedi e cambiala subito!",
    )

    return {"message": "User registered successfully", "password": password}


@router.get(
    "",
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


@router.get(
    "/me",
    response_model=schemas.User,
    status_code=status.HTTP_200_OK,
)
async def get_user(
    current_user=Depends(verify_user),
    user_repo: UserRepository = Depends(get_user_repository),
):
    """
    Restituisce dell'utente che richiede l'operazione.
    """
    # Ottiene i dati dell'utente
    user = await user_repo.get_by_email(current_user.get("sub"))

    # Ritorna i dati dell'utente se esistente, altrimenti solleva un'eccezione 404
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user


# TODO: non si dovrebbe poter cambiare la password senza reinserire quella attuale
@router.put(
    "",
    status_code=status.HTTP_200_OK,
)
async def update_user(
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
    # Aggiorna i dati dell'utente nel database
    try:
        result = await user_repo.update_user(
            user_id=user_new_data.id,
            user_data=user_new_data,
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


@router.delete(
    "",
    status_code=status.HTTP_200_OK,
)
async def delete_user(
	delete_user: schemas.UserDelete,
    admin: schemas.UserAuth,
    current_user=Depends(verify_admin),
    user_repository: UserRepository = Depends(get_user_repository),
):
    """
    Elimina un utente esistente se la password inserita dall'admin è corretta.
    """
    try:
        # Verifica che l'admin esista e che la password sia corretta
        valid_user = await authenticate_user(
            current_user.get("sub"), admin.current_password, user_repository
        )
        print(f"valid_user: {valid_user}")
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

        await user_repository.delete_user(
            user_id=delete_user.id,
        )
    except HTTPException as e:
        raise e
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete user: {e}",
        )
    return {"message": "User deleted successfully"}


@router.patch(
    "/password",
    status_code=status.HTTP_200_OK,
)
async def update_password(
    user_data: schemas.UserUpdatePassword,
    current_user=Depends(verify_user),
    user_repository: UserRepository = Depends(get_user_repository),
):
    """
    Aggiorna la password dell'utente.
    """
    # Aggiorna la password dell'utente
    try:
        # Verifica che l'utente esista e che la password sia corretta
        user_current_data = await user_repository.get_by_email(current_user.get("sub"))
        if not verify_password(
            user_data.current_password, user_current_data.get("hashed_password")
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Wrong password",
            )
        # Aggiorna la password
        initialized = None
        if user_current_data.get("is_initialized") is False:
            initialized = True

        await user_repository.update_user(
            user_id=current_user.get("sub"),
            user_data=schemas.UserUpdate(
                password=user_data.password,
                is_initialized=initialized,
            ),
        )
    except Exception as e:
        print(f"Error updating password: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update password: {e}",
        )

    return {"message": "Password updated successfully"}
