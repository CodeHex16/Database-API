from fastapi import APIRouter, status, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo.errors import DuplicateKeyError
from bson import ObjectId
from bson.errors import InvalidId

import app.schemas as schemas
from typing import List
from app.database import get_db
from app.repositories.faq_repository import FaqRepository
from app.routes.auth import verify_admin

router = APIRouter(prefix="/faqs", tags=["faq"])


def get_faq_repository(db: AsyncIOMotorDatabase = Depends(get_db)):
    return FaqRepository(db)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
)
async def create_faq(
    faq: schemas.FAQ,
    current_user=Depends(verify_admin),
    faq_repo: FaqRepository = Depends(get_faq_repository),
):
    """
    Crea una nuova FAQ.

    Args:
    * **faq (schemas.FAQ)**: La FAQ da creare.
    * **current_user**: L'utente che ha creato la FAQ, dovrà essere un _admin_ per poter svolgere questa operazione; verrà salvato come _author_email_ nel database.
    * **faq_repo (FaqRepository)**: Il repository delle FAQ.
    """
    try:
        await faq_repo.insert_faq(faq=faq, author_email=current_user.get("sub"))
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

    return status.HTTP_201_CREATED


@router.get(
    "",
    response_model=List[schemas.FAQResponse],
)
async def get_faqs(
    current_user=Depends(verify_admin),
    faq_repo: FaqRepository = Depends(get_faq_repository),
):
    """
    Restituisce una lista di tutte le FAQ.
    """
    faqs = await faq_repo.get_faqs()

    # Ritorna la lista di user se esistente, altrimenti solleva un'eccezione 404
    if not faqs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No faqs found",
        )
    return faqs


@router.put(
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

    return status.HTTP_200_OK


@router.delete(
    "/{faq_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_faq(
    faq_id: str,
    current_user=Depends(verify_admin),
    faq_repo: FaqRepository = Depends(get_faq_repository),
):
    """
    Cancella una FAQ.
    """
    try:
        await faq_repo.delete_faq(faq_id=ObjectId(faq_id))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}",
        )

    return status.HTTP_200_OK
