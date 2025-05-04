from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from bson import ObjectId
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
from app.utils import get_object_id

router = APIRouter(
    prefix="/documents",
    tags=["document"],
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


@router.post("", status_code=status.HTTP_201_CREATED)
async def upload_document(
    document: schemas.Document,
    current_user=Depends(verify_admin),
    document_repository=Depends(get_document_repository),
):
    """
    Carica un documento nel database.

    ### Args:
    * **document (schemas.Document)**: Il documento da caricare.

    ### Raises:
    * **HTTPException.HTTP_400_BAD_REQUEST**: Se il documento esiste già o si verifica un errore durante l'inserimento.
    * **HTTPException.HTTP_500_INTERNAL_SERVER_ERROR**: Se si verifica un errore durante l'upload del file.
    * **DuplicateKeyError**: Se il documento esiste già nel database.
    """
    try:
        await document_repository.insert_document(
            owner_email=current_user.get("sub"), document=document
        )
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


@router.get(
    "", response_model=List[schemas.DocumentResponse], status_code=status.HTTP_200_OK
)
async def get_documents(
    current_user=Depends(verify_admin),
    document_repository=Depends(get_document_repository),
):
    """
    Restituisce la lista di tutti i documenti.

    ### Returns:
    * **List[schemas.DocumentResponse]**: La lista dei documenti.

    ### Raises:
    * **HTTPException.HTTP_404_NOT_FOUND**: Se non ci sono documenti nel database.
    * **HTTPException.HTTP_500_INTERNAL_SERVER_ERROR**: Se si verifica un errore durante il recupero dei documenti.
    """

    documents = await document_repository.get_documents()

    if not documents:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nessun documento trovato",
        )

    return documents


@router.delete("/{file_path}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    file_path: str,
    admin: schemas.UserAuth,
    current_user=Depends(verify_admin),
    document_repository=Depends(get_document_repository),
    user_repository: UserRepository = Depends(get_user_repository),
):
    """
    Elimina un documento dal database.

    ### Args:
    * **file_path**: Il percorso del file da eliminare.
    * **admin (schemas.UserAuth)**: Le credenziali dell'amministratore.

    ### Raises:
    * **HTTPException.HTTP_401_UNAUTHORIZED**: Se le credenziali non sono valide.
    * **HTTPException.HTTP_403_FORBIDDEN**: Se l'utente non è autorizzato a eliminare il documento.
    * **HTTPException.HTTP_404_NOT_FOUND**: Se il documento non viene trovato.
    * **HTTPException.HTTP_500_INTERNAL_SERVER_ERROR**: Se si verifica un errore durante l'eliminazione del documento.
    """

    # Verifica se l'admin ha reinserito correttamente la propria password
    valid_user = await authenticate_user(
        current_user.get("sub"), admin.current_password, user_repository
    )
    if not valid_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenziali non valide",
        )
    # Ensure the user confirming is the same as the one from the token
    if valid_user.get("_id") != current_user.get("sub"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Credentials do not match the logged-in admin",
        )

    try:
        file_id = get_object_id(file_path)
        result = await document_repository.delete_document(file_id=file_id)
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
