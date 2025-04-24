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
from app.repositories.user_repository import UserRepository
import app.schemas as schemas
from app.routes.auth import (
    verify_admin,
    verify_user,
    authenticate_user,
    get_user_repository,
)

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


@router.get("/", response_model=List[schemas.Document], status_code=status.HTTP_200_OK)
async def get_documents(
    current_user=Depends(verify_admin),
    document_repository=Depends(get_document_repository),
):
    """
    Restituisce la lista di tutti i documenti.
    """

    documents = await document_repository.get_documents()

    if not documents:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nessun documento trovato",
        )

    return documents


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
    admin: schemas.UserAuth,
    current_user=Depends(verify_admin),
    document_repository=Depends(get_document_repository),
    user_repository: UserRepository = Depends(get_user_repository),
):
    """
    Elimina un documento dal database.

    Args:
        file_path (str): Il percorso del file da eliminare.
        admin (schemas.UserEmailPwd): Credentials of the admin confirming the action.
        current_user: The verified admin user from the token.
        document_repository: Injected document repository.
        user_repository: Injected user repository.

    Returns:
        status.HTTP_200_OK: Se il documento è stato eliminato con successo.

    Raises:
        HTTPException: Se le credenziali non sono valide, il documento non esiste o si verifica un errore.
    """

    # Verifica se l'admin ha reinserito correttamente la propria password
    valid_user = await authenticate_user(admin.email, admin.password, user_repository)
    if not valid_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenziali non valide",
        )
    # Ensure the user confirming is the same as the one from the token
    if valid_user["_id"] != current_user.get("sub"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Credentials do not match the logged-in admin",
        )

    try:
        result = await document_repository.delete_document(file_path)
        if result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Documento non trovato",
            )
    except Exception as e:
        print(f"Error deleting document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Eliminazione del file fallita: {e}",
        )
    return {"message": "Documento eliminato con successo"}
