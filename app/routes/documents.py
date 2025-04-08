import os
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from typing import List, Optional
from datetime import datetime
from pydantic import EmailStr
import requests
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo.errors import DuplicateKeyError

from app.database import get_db
from app.repositories.document_repository import DocumentRepository
import app.schemas as schemas
from app.routes.auth import verify_admin, verify_user

router = APIRouter(
    prefix="/documents",
    tags=["documents"],
)


def get_document_repository(db: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Restituisce un'istanza del repository dei documenti.

    Args:
        db (AsyncIOMotorDatabase): Il database MongoDB.

    Returns:
        DocumentRepository: Un'istanza del repository dei documenti.
    """
    return DocumentRepository(db)


@router.post("/upload")
async def upload_document(
    document: schemas.Document,
    current_user=Depends(verify_admin),
    document_repository=Depends(get_document_repository),
):
    """
    Carica un documento nel database.

    Args:
        document (schemas.Document): Il documento da caricare.

    Returns:
        status.HTTP_201_CREATED: Se il documento è stato caricato con successo.

    Raises:
        HTTPException: Se il documento già esiste o se si verifica un errore durante il caricamento.
    """
    document.owner_email = current_user.get("sub")
    try:
        await document_repository.insert_document(document)
    except DuplicateKeyError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Documento già esistente",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload del file fallito: {e}",
        )
    return status.HTTP_201_CREATED
