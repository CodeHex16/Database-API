import os
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo.errors import DuplicateKeyError
from jose import jwt, JWTError

from app.database import get_db
import app.schemas as schemas
from app.routes.auth import (
    verify_admin,
    verify_user,
    authenticate_user,
)
from app.repositories.user_repository import UserRepository, get_user_repository

from app.utils import get_password_hash, verify_password
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
    Registra un nuovo utente.

    ### Args:
    * **user_data**: I dati dell'utente da registrare.

    ### Raises:
    * **HTTPException.HTTP_400_BAD_REQUEST**: Se l'email è già in uso.
    * **HTTPException.HTTP_500_INTERNAL_SERVER_ERROR**: Se si verifica un errore durante la registrazione dell'utente.

    ### Returns:
    * **dict**: Un messaggio di successo e la password temporanea generata.
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
)
async def get_users(
    current_user=Depends(verify_admin),
    user_repo: UserRepository = Depends(get_user_repository),
):
    """
    Restituisce una lista di tutti gli utenti registrati.

    ### Returns:
    * **List[schemas.User]**: La lista degli utenti registrati.

    ### Raises:
    * **HTTPException.HTTP_404_NOT_FOUND**: Se non sono stati trovati utenti.
    * **HTTPException.HTTP_500_INTERNAL_SERVER_ERROR**: Se si verifica un errore durante il recupero degli utenti.
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
)
async def get_user(
    current_user=Depends(verify_user),
    user_repo: UserRepository = Depends(get_user_repository),
):
    """
    Restituisce i dati dell'utente che richiede l'operazione.

    ### Returns:
    * **schemas.User**: I dati dell'utente.

    ### Raises:
    * **HTTPException.HTTP_404_NOT_FOUND**: Se l'utente non è stato trovato.
    * **HTTPException.HTTP_500_INTERNAL_SERVER_ERROR**: Se si verifica un errore durante il recupero dell'utente.
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


@router.patch(
    "",
    status_code=status.HTTP_200_OK,
)
async def update_user(
    user_new_data: schemas.UserUpdate,
    current_user=Depends(verify_admin),
    user_repo: UserRepository = Depends(get_user_repository),
):
    """
    Aggiorna i dati di un utente esistente.

    ### Args:
    * **user_new_data**: I nuovi dati dell'utente da aggiornare.

    ### Raises:
    * **HTTPException.HTTP_400_BAD_REQUEST**: Se l'email è già in uso.
    * **HTTPException.HTTP_404_NOT_FOUND**: Se l'utente non è stato trovato.
    * **HTTPException.HTTP_500_INTERNAL_SERVER_ERROR**: Se si verifica un errore durante l'aggiornamento dell'utente.
    * **HTTPException.HTTP_304_NOT_MODIFIED**: Se i dati forniti corrispondono a quelli esistenti.
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
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_user(
    delete_user: schemas.UserDelete,
    admin: schemas.UserAuth,
    current_user=Depends(verify_admin),
    user_repository: UserRepository = Depends(get_user_repository),
):
    """
    Elimina un utente esistente.

    ### Args:
    * **delete_user**: I dati dell'utente da eliminare.
    * **admin**: I dati dell'amministratore che richiede l'operazione.

    ### Raises:
    * **HTTPException.HTTP_401_UNAUTHORIZED**: Se le credenziali dell'amministratore non sono valide.
    * **HTTPException.HTTP_403_FORBIDDEN**: Se le credenziali non corrispondono all'amministratore loggato.
    * **HTTPException.HTTP_404_NOT_FOUND**: Se l'utente non è stato trovato.
    * **HTTPException.HTTP_500_INTERNAL_SERVER_ERROR**: Se si verifica un errore durante l'eliminazione dell'utente.
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

    ### Args:
    * **user_data**: I dati dell'utente da aggiornare.

    ### Raises:
    * **HTTPException.HTTP_401_UNAUTHORIZED**: Se la password corrente non è corretta.
    * **HTTPException.HTTP_404_NOT_FOUND**: Se l'utente non è stato trovato.
    * **HTTPException.HTTP_500_INTERNAL_SERVER_ERROR**: Se si verifica un errore durante l'aggiornamento della password.
    * **HTTPException.HTTP_304_NOT_MODIFIED**: Se la password fornita corrisponde a quella esistente.
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
                _id=current_user.get("sub"),
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


@router.post(
    "/password_reset",
    status_code=status.HTTP_200_OK,
)
async def reset_password(
    user_data: schemas.UserForgotPassword,
    user_repository: UserRepository = Depends(get_user_repository),
):
    """
    Resetta la password dell'utente e invia un'email con la nuova password temporanea.

    ### Args:
    * **user_data**: I dati dell'utente di cui resettare la password.

    ### Raises:
    * **HTTPException.HTTP_404_NOT_FOUND**: Se l'utente non è stato trovato.
    * **HTTPException.HTTP_500_INTERNAL_SERVER_ERROR**: Se si verifica un errore durante il reset della password.
    * **HTTPException.HTTP_400_BAD_REQUEST**: Se i nuovi dati non sono validi.
    """
    try:
        user = await user_repository.get_by_email(user_data.email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        password = os.urandom(16).hex()

        await user_repository.update_user(
            user_id=user_data.email,
            user_data=schemas.UserUpdate(
                _id=user_data.email,
                password=password,
                is_initialized=False,
            ),
        )

        # Invia l'email con il token
        await EmailService().send_email(
            to=[user.get("_id")],
            subject="[Suppl-AI] Password Reset",
            body=f"Ciao {user.get('name')},\n\nEcco la tua nuova password temporanea:\n\n{password}\n\nAccedi e cambiala subito!",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send password reset email: {e}",
        )
