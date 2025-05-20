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

style = """<style>
                        body {
                        background-color: #f8f9fa;
                        font-family: 'Roboto', sans-serif;
                        margin: 0;
                        padding: 0;
                        color: #212121;
                        }
                        .container {
                        max-width: 600px;
                        margin: 2rem auto;
                        background: #fff;
                        border-radius: 8px;
                        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
                        padding: 2rem;
                        }
                        .header {
                        text-align: center;
                        margin-bottom: 1rem;
                        }
                        .title {
                        font-size: 1.5rem;
                        font-weight: 500;
                        }
                        .content {
                        margin: 1rem 0;
                        line-height: 1.6;
                        }
                        .password-box {
                        background-color: #e3f2fd;
                        padding: 1rem;
                        font-size: 1.25rem;
                        font-weight: bold;
                        border-radius: 6px;
                        text-align: center;
                        color: #0d47a1;
                        letter-spacing: 0.5px;
                        }
                        .btn {
                        display: inline-block;
                        background-color: #1976d2;
                        color: #fff !important;
                        padding: 0.75rem 1.5rem;
                        text-decoration: none;
                        border-radius: 24px;
                        font-weight: 500;
                        transition: background 0.3s ease;
                        }
                        .btn:hover {
                        background-color: #1565c0;
                        }
                        .footer {
                        text-align: center;
                        font-size: 0.875rem;
                        margin-top: 2rem;
                        color: #666;
                        }
                        .icon-links {
                        margin-top: 1rem;
                        text-align: center;
                        }
                        .icon-links a {
                        margin: 0 0.5rem;
                        display: inline-block;
                        text-decoration: none;
                        }
                        .icon-links img {
                        width: 24px;
                        height: 24px;
                        vertical-align: middle;
                        filter: grayscale(100%);
                        transition: filter 0.3s;
                        }
                        .icon-links img:hover {
                        filter: grayscale(0%);
                        }
                    </style>
"""

SECRET_KEY_JWT = os.getenv("SECRET_KEY_JWT") or "$2b$12$zqt9Rgv1PzORjG5ghJSb6OSdYrt7f7cLc38a21DgX/DMyqt80AUCi"
ALGORITHM = "HS256"

def security_check(): # pragma: no cover
    if SECRET_KEY_JWT == "$2b$12$zqt9Rgv1PzORjG5ghJSb6OSdYrt7f7cLc38a21DgX/DMyqt80AUCi":
        print(
            "WARNING: SECRET_KEY_JWT is not set. Using default value for development purposes only."
        )
        print("Please set SECRET_KEY_JWT in your environment variables.")
security_check()


@router.post("",status_code=status.HTTP_201_CREATED)
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
            detail="Esiste già un utente con questa email",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {e}",
        )

    try:
        await EmailService().send_email(
            to=[user_data.email],
            subject=f"[Suppl-AI] Registrazione utente",
            body=f"""
            <!DOCTYPE html>
                <html lang="it">
                <head>
                <meta charset="UTF-8" />
                <meta name="viewport" content="width=device-width, initial-scale=1.0" />
                <title>Registrazione utente</title>
               {style}
                </head>
                <body>
                <div class="container">
                    <div class="header">
                    <div class="title" style="font-size: 2rem; font-weight: 700; color: #1976d2;">SUPPL-AI</div>
                    </div>
                    <div class="content">
                    <p><strong>Benvenuto in Suppl-AI!</strong></p>
                    <p>Ecco la tua password temporanea:</p>
                    <div class="password-box">{password}</div>
                    <p>Accedi e cambiala subito!</p>
                    </div>

                    <div class="icon-links">
                    <a href="https://codehex16.github.io/" title="Sito Web">
                        <img src="https://img.icons8.com/ios-filled/50/000000/domain.png" alt="Sito">
                    </a>
                    <a href="https://github.com/codehex16" title="GitHub">
                        <img src="https://img.icons8.com/ios-filled/50/000000/github.png" alt="GitHub">
                    </a>
                    </div>

                    <div class="footer">
                    Questo progetto &egrave; realizzato da <strong>CodeHex16</strong>, gruppo 16 del Progetto di SWE dell'Universit&agrave; degli Studi di Padova.
                    </div>
                </div>
                </body>
                </html>
                """
            # body=f"Benvenuto in Suppl-AI!\nEcco la tua password temporanea\n\n{password}\n\n Accedi e cambiala subito!",
        )
    except Exception as e:
        raise HTTPException(
        	status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        	detail=f"Failed to send email to user: {e}",
        )
        # print(f"  Error: Failed to send to user the password: {e}")

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
    user_new_data.password = None
    # Verifica che l'admin esista e che la password sia corretta
    valid_user = await authenticate_user(
        current_user.get("sub"), user_new_data.admin_password, user_repo
    )
    if not valid_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin password",
        )
    
    # Aggiorna i dati dell'utente nel database
    result = await user_repo.update_user(
        user_id=user_new_data.id,
        user_data=user_new_data,
    )

    if result.modified_count == 0 and result.matched_count > 0:
        return {"message": "User data is already up to date."}
    elif result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found during update attempt",
        )
    else:
        return {"message": "User updated successfully."}



@router.delete("",status_code=status.HTTP_204_NO_CONTENT)
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

        result = await user_repository.update_user(
            user_id=current_user.get("sub"),
            user_data=schemas.UserUpdate(
                _id=current_user.get("sub"),
                password=user_data.password,
                is_initialized=initialized,
            ),
        )
        if result.matched_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found during password update attempt",
            )
        else:
            return {"message": "Password updated successfully"}
        
    except Exception as e:
        print(f"Error updating password: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update password: {e}",
        )

    


@router.post(
    "/password_reset",
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

       
        try:
            # Invia l'email con il token
            await EmailService().send_email(
                to=[user_data.email],
                subject="[Suppl-AI] Password Reset",
                body=f"""
                <!DOCTYPE html>
                    <html lang="it">
                    <head>
                    <meta charset="UTF-8" />
                    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
                    <title>Password Reset</title>
                    {style}
                    </head>
                    <body>
                    <div class="container">
                        <div class="header">
                        <div class="title" style="font-size: 2rem; font-weight: 700; color: #1976d2;">SUPPL-AI</div>
                        <div class="title">Ciao {user.get('name')},</div>
                        </div>
                        <div class="content">
                        Ecco la tua nuova password temporanea:
                        <div class="password-box">{password}</div>
                        <p>Accedi e cambiala subito per mantenere il tuo account sicuro.</p>
                        </div>

                        <div class="icon-links">
                        <a href="https://codehex16.github.io/" title="Sito Web">
                            <img src="https://img.icons8.com/ios-filled/50/000000/domain.png" alt="Sito">
                        </a>
                        <a href="https://github.com/codehex16" title="GitHub">
                            <img src="https://img.icons8.com/ios-filled/50/000000/github.png" alt="GitHub">
                        </a>
                        </div>

                        <div class="footer">
                        Questo progetto &egrave; realizzato da <strong>CodeHex16</strong>, gruppo 16 del Progetto di SWE dell'Universit&agrave; degli Studi di Padova.
                        </div>
                    </div>
                    </body>
                    </html>
                """
                # body=f"Ciao {user.get('name')},\n\nEcco la tua nuova password temporanea:\n\n{password}\n\nAccedi e cambiala subito!",
            )
        except Exception as e:
            # raise HTTPException(
            #     status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            #     detail=f"Failed to send email to user: {e}",
            # )
            print("  Error: Failed to send to user the password")

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send password reset email: {e}",
        )
    return {"message": "Password reset email sent successfully", "password": password}
