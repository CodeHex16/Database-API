from fastapi import APIRouter, status, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo.errors import DuplicateKeyError
from bson import ObjectId
from bson.errors import InvalidId
from datetime import datetime

import app.schemas as schemas
from typing import List
from app.database import get_db
from app.repositories.faq_repository import FaqRepository
from app.routes.auth import verify_admin

router = APIRouter(prefix="/faq", tags=["faq"])


def get_faq_repository(db: AsyncIOMotorDatabase = Depends(get_db)):
    return FaqRepository(db)


@router.get(
    "/",
    response_model=List[schemas.FAQ],
    status_code=status.HTTP_200_OK,
)
async def get_faqs(
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


@router.post(
    "/create",
    status_code=status.HTTP_201_CREATED,
)
async def create_faq(
    faq: schemas.FAQ,
    current_user=Depends(verify_admin),
    faq_repo: FaqRepository = Depends(get_faq_repository),
):
    """
    Crea una nuova FAQ.
    """
    try:
        await faq_repo.insert_faq(faq)
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


@router.put(
    "/update",
)
async def update_faq(
    faq: schemas.FAQUpdate,
    current_user=Depends(verify_admin),
    faq_repo: FaqRepository = Depends(get_faq_repository),
):
    """
    Aggiorna una FAQ esistente.
    """
    # Ottiene i dati della FAQ esistente
    faq_current_data = await faq_repo.get_faq_by_id(faq_id=ObjectId(faq.id))

    # Controla se la FAQ esiste
    if not faq_current_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="FAQ not found",
        )

    if (
        faq.title != faq_current_data.get("title")
        or faq.question != faq_current_data.get("question")
        or faq.answer != faq_current_data.get("answer")
        or faq.author_email != faq_current_data.get("author_email")
    ):
        # Prepara i dati per l'aggiornamento
        update_payload = {
            "id": ObjectId(faq.id),
            "title": (faq.title if faq.title else faq_current_data.get("title")),
            "question": (
                faq.question if faq.question else faq_current_data.get("question")
            ),
            "answer": (faq.answer if faq.answer else faq_current_data.get("answer")),
            "author_email": (
                faq.author_email
                if faq.author_email
                else faq_current_data.get("author_email")
            ),
            "updated_at": faq.updated_at,
        }
    else:
        print("FAQ data is already up to date.")
        raise HTTPException(
            status_code=status.HTTP_304_NOT_MODIFIED,
            detail="FAQ data is already up to date.",
        )

    # Aggiorna i campi della FAQ
    try:
        await faq_repo.update_faq(faq=update_payload)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}",
        )

    return status.HTTP_200_OK


@router.delete(
    "/delete",
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
        await faq_repo.delete_faq(faq_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}",
        )

    return status.HTTP_200_OK
