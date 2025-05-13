from fastapi import APIRouter, status, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo.errors import DuplicateKeyError
from bson import ObjectId

import app.schemas as schemas
from typing import List
from app.repositories.faq_repository import FaqRepository, get_faq_repository
from app.repositories.user_repository import UserRepository, get_user_repository
from app.routes.auth import verify_admin, authenticate_user, verify_user

router = APIRouter(prefix="/faqs", tags=["faq"])


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_faq(
    faq: schemas.FAQ,
    current_user=Depends(verify_admin),
    faq_repo: FaqRepository = Depends(get_faq_repository),
):
    """
    Crea una nuova FAQ.

    ### Args:
    * **faq (schemas.FAQ)**: La FAQ da creare.

    ### Returns:
    * **id**: L'ID della FAQ appena creata.

    ### Raises:
    * **HTTPException.HTTP_400_BAD_REQUEST**: Se la FAQ esiste già o si verifica un errore durante l'inserimento.
    * **HTTPException.HTTP_500_INTERNAL_SERVER_ERROR**: Se si verifica un errore durante l'inserimento.
    * **DuplicateKeyError**: Se la FAQ esiste già nel database.
    """
    try:
        inserted = await faq_repo.insert_faq(
            faq=faq, author_email=current_user.get("sub")
        )
    except DuplicateKeyError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="FAQ with the same title already exists",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}",
        )

    return {
        "id": str(inserted),
        "status": status.HTTP_201_CREATED,
    }


@router.get("", response_model=List[schemas.FAQResponse])
async def get_faqs(
    current_user=Depends(verify_user),
    faq_repo: FaqRepository = Depends(get_faq_repository),
):
    """
    Restituisce una lista di tutte le FAQ.

    ### Returns:
    * **result (List[schemas.FAQResponse])**: Lista di FAQ.

    ### Raises:
    * **HTTPException.HTTP_404_NOT_FOUND**: Se non ci sono FAQ nel database.
    """
    faqs = await faq_repo.get_faqs()

    # Ritorna la lista di user se esistente, altrimenti solleva un'eccezione 404
    if not faqs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No faqs found",
        )
    return faqs


@router.patch(
    "/{faq_id}",
)
async def update_faq(
    faq_id: str,
    faq: schemas.FAQUpdate,
    current_user=Depends(verify_admin),
    faq_repo: FaqRepository = Depends(get_faq_repository),
):
    """
    Aggiorna una FAQ esistente.

    ### Args:
    * **faq_id**: L'ID della FAQ da aggiornare.
    * **faq (schemas.FAQUpdate)**: I dati della FAQ da aggiornare.
    
    ### Raises:
    * **HTTPException.HTTP_304_NOT_MODIFIED**: Se la FAQ non esiste o se i dati non sono cambiati.
    * **HTTPException.HTTP_500_INTERNAL_SERVER_ERROR**: Se si verifica un errore durante l'aggiornamento.
    """
    # Aggiorna i campi della FAQ
    try:
        await faq_repo.update_faq(
            faq_id=ObjectId(faq_id), faq_data=faq, author_email=current_user.get("sub")
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}",
        )


@router.delete("/{faq_id}",status_code=status.HTTP_204_NO_CONTENT)
async def delete_faq(
    faq_id: str,
    admin: schemas.UserAuth,
    current_user=Depends(verify_admin),
    faq_repo: FaqRepository = Depends(get_faq_repository),
    user_repository: UserRepository = Depends(get_user_repository),
):
    """
    Cancella una FAQ.

    ### Args:
    * **faq_id**: L'ID della FAQ da cancellare.
    * **admin (schemas.UserAuth)**: La conferma della password dell'admin necessaria per l'eliminazione.

    ### Raises:
    * **HTTPException.HTTP_401_UNAUTHORIZED**: Se le credenziali non sono valide.
    * **HTTPException.HTTP_403_FORBIDDEN**: Se le credenziali non corrispondono all'admin loggato.
    * **HTTPException.HTTP_500_INTERNAL_SERVER_ERROR**: Se si verifica un errore durante l'eliminazione.
    """
    # Verifica che l'admin esista e che la password sia corretta
    valid_user = await authenticate_user(
        current_user.get("sub"), admin.current_password, user_repository
    )
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

    try:
        await faq_repo.delete_faq(faq_id=ObjectId(faq_id))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}",
        )
