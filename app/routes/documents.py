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

@router.delete("/delete")
async def delete_document(
    file_path: str,
    current_user=Depends(verify_admin),
    document_repository=Depends(get_document_repository),
):
    """
    Elimina un documento dal database.

    Args:
        file_path (str): Il percorso del file da eliminare.
        current_user: L'utente corrente, verificato come admin.

    Returns:
        status.HTTP_200_OK: Se il documento è stato eliminato con successo.

    Raises:
        HTTPException: Se il documento non esiste o se si verifica un errore durante l'eliminazione.
    """
    try:
        await document_repository.delete_document(file_path)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Eliminazione del file fallita: {e}",
        )
    return status.HTTP_200_OK