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
    # Aggiorna i campi della FAQ
    try:
        await faq_repo.update_faq(faq=faq, author_email=current_user.get("sub"))
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
