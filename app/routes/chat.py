from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from bson import ObjectId

from app.database import get_db
from app.repositories.chat_repository import ChatRepository
import app.schemas as schemas
from app.routes.auth import (
    verify_user,
    verify_admin,
)

router = APIRouter(
    prefix="/chats",
    tags=["chat"],
)


def get_chat_repository(db=Depends(get_db)):
    return ChatRepository(db)


@router.get(
    "/new_chat",
)
async def get_new_chat(
    current_user=Depends(verify_user),
    chat_repository=Depends(get_chat_repository),
):
    """
    Crea una nuova chat per l'utente autenticato.

    ### Returns:
    * **chat_id**: ID della chat appena creata.

    ### Raises:
    * **HTTPException.HTTP_400_BAD_REQUEST**: Se l'utente non è autenticato o se si verifica un errore durante la creazione della chat.
    * **HTTPException.HTTP_500_INTERNAL_SERVER_ERROR**: Se si verifica un errore durante la creazione della chat.
    * **HTTPException.HTTP_404_NOT_FOUND**: Se non viene trovata la chat.
    """
    user_email = current_user.get("sub")

    if not user_email:
        raise HTTPException(status_code=400, detail="Invalid user information in token")

    chats = await chat_repository.initialize_chat(user_email)

    return {"chat_id": str(chats["_id"])}


@router.get("", response_model=List[schemas.ChatResponse])
async def get_chats(
    current_user=Depends(verify_user),
    chat_repository=Depends(get_chat_repository),
):
    """
    Recupera i metadati delle chat dell'utente autenticato.

    ### Returns:
    * **reuslt (List[ChatResponse])**: Lista di chat dell'utente.

    ### Raises:
    * **HTTPException.HTTP_400_BAD_REQUEST**: Se l'utente non è autenticato o se si verifica un errore durante il recupero delle chat.
    * **HTTPException.HTTP_500_INTERNAL_SERVER_ERROR**: Se si verifica un errore durante il recupero delle chat.
    * **HTTPException.HTTP_404_NOT_FOUND**: Se non vengono trovate chat.
    """

    # Verifica il token e ottieni l'email dell'utente
    user_email = current_user.get("sub")

    if not user_email:
        raise HTTPException(status_code=400, detail="Invalid user information in token")

    chats = await chat_repository.get_chat_by_user_email(user_email)

    result = []

    for chat in chats:
        result.append(
            {
                "id": str(chat["_id"]),
                "name": chat.get("name", "Chat senza nome"),
                "user_email": chat.get("user_email"),
                "created_at": chat.get("created_at"),
            }
        )

    return result


@router.patch("/{chat_id}/name")
async def change_chat_name(
    chat_id: str,
    new_name: str,
    current_user=Depends(verify_user),
    chat_repository=Depends(get_chat_repository),
):
    """
    Modifica il nome della chat.

    ### Args:
    * **chat_id(str)**: ID della chat da modificare.
    * **new_name(str)**: Nuovo nome da assegnare alla chat.

    ### Raises:
    * **HTTPException.HTTP_400_BAD_REQUEST**: Se l'utente non è autenticato o se si verifica un errore durante la modifica del nome della chat.
    * **HTTPException.HTTP_500_INTERNAL_SERVER_ERROR**: Se si verifica un errore durante la modifica del nome della chat.
    * **HTTPException.HTTP_404_NOT_FOUND**: Se non viene trovata la chat.
    """
    user_email = current_user.get("sub")

    # Verifica che la chat esista e appartenga all'utente
    existing_chat = await chat_repository.get_chat_by_id(chat_id, user_email)
    if not existing_chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    await chat_repository.update_chat(chat_id, {"name": new_name})


@router.delete("/{chat_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chat(
    chat_id: str,
    current_user=Depends(verify_user),
    chat_repository=Depends(get_chat_repository),
):
    """
    Elimina una chat esistente.

    ### Args:
    * **chat_id**: ID della chat da eliminare.

    ### Raises:
    * **HTTPException.HTTP_400_BAD_REQUEST**: Se l'utente non è autenticato o se si verifica un errore durante l'eliminazione della chat.
    * **HTTPException.HTTP_500_INTERNAL_SERVER_ERROR**: Se si verifica un errore durante l'eliminazione della chat.
    * **HTTPException.HTTP_404_NOT_FOUND**: Se non viene trovata la chat.
    """
    user_email = current_user.get("sub")

    # Verifica che la chat esista e appartenga all'utente
    existing_chat = await chat_repository.get_chat_by_id(chat_id, user_email)
    if not existing_chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    await chat_repository.delete_chat(chat_id, user_email)


@router.post(
    "/{chat_id}/messages",
    response_model=schemas.Message,
    status_code=status.HTTP_201_CREATED,
)
async def add_message_to_chat(
    chat_id: str,
    message: schemas.MessageCreate,
    current_user=Depends(verify_user),
    chat_repository=Depends(get_chat_repository),
):
    """
    Aggiunge un messaggio ad una chat esistente.

    ### Args:
    * **chat_id**: ID della chat a cui aggiungere il messaggio.
    * **message**: Messaggio da aggiungere (contenuto e mittente).

    ### Returns:
    * **message_data**: Messaggio aggiunto (contenuto, mittente e timestamp).

    ### Raises:
    * **HTTPException.HTTP_400_BAD_REQUEST**: Se l'utente non è autenticato o se si verifica un errore durante l'aggiunta del messaggio.
    * **HTTPException.HTTP_500_INTERNAL_SERVER_ERROR**: Se si verifica un errore durante l'aggiunta del messaggio.
    * **HTTPException.HTTP_404_NOT_FOUND**: Se non viene trovata la chat.
    """
    user_email = current_user.get("sub")

    # Verifica che la chat esista e appartenga all'utente
    existing_chat = await chat_repository.get_chat_by_id(chat_id, user_email)
    if not existing_chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    # Aggiungi il messaggio alla chat
    message_data = await chat_repository.add_message(chat_id, message)

    return message_data


@router.get("/{chat_id}/messages", response_model=schemas.ChatMessages)
async def get_chat_messages(
    chat_id: str,
    current_user=Depends(verify_user),
    chat_repository=Depends(get_chat_repository),
):
    """
    Recupera i messaggi di una chat esistente.

    ### Args:
    * **chat_id**: ID della chat di cui recuperare i messaggi.

    ### Returns:
    * **result (ChatMessages)**: Nome della chat e lista dei messaggi contenuti in quella chat.

    ### Raises:
    * **HTTPException.HTTP_400_BAD_REQUEST**: Se l'utente non è autenticato o se si verifica un errore durante il recupero dei messaggi.
    * **HTTPException.HTTP_500_INTERNAL_SERVER_ERROR**: Se si verifica un errore durante il recupero dei messaggi.
    * **HTTPException.HTTP_404_NOT_FOUND**: Se non viene trovata la chat.
    """
    user_email = current_user.get("sub")

    # Verifica che la chat esista e appartenga all'utente
    existing_chat = await chat_repository.get_chat_by_id(chat_id, user_email)
    if not existing_chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    result = {
        "name": existing_chat.get("name", "Chat senza nome"),
        "messages": existing_chat.get("messages", []),
    }

    return result


@router.patch("/{chat_id}/messages/{message_id}/rating")
async def rate_message(
    chat_id: str,
    message_id: str,
    rating: bool,
    current_user=Depends(verify_user),
    chat_repository=Depends(get_chat_repository),
):
    """
    Aggiunge una valutazione ad un messaggio esistente in una chat.

    ### Args:
    * **chat_id**: ID della chat contenente il messaggio.
    * **message_id**: ID del messaggio da valutare.
    * **rating**: Valutazione da assegnare al messaggio (True o False).

    ### Raises:
    * **HTTPException.HTTP_304_NOT_MODIFIED**: Se la valutazione del messaggio non è cambiata.
    * **HTTPException.HTTP_404_NOT_FOUND**: Se non viene trovata la chat o il messaggio.
    * **HTTPException.HTTP_500_INTERNAL_SERVER_ERROR**: Se si verifica un errore durante la valutazione del messaggio.
    """
    user_email = current_user.get("sub")

    # Verifica che la chat esista e appartenga all'utente
    existing_chat = await chat_repository.get_chat_by_id(chat_id, user_email)
    if not existing_chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    # Aggiorna la valutazione del messaggio
    try:
        result = await chat_repository.update_message_rating(ObjectId(chat_id), ObjectId(message_id), rating)

        print(f"Result: {result}")
        if result.matched_count == 0:
            raise HTTPException(
                status_code=404,
            )
        if result.modified_count == 0:
            raise HTTPException(
                status_code=304,
                detail="Message rating already updated",
            )
    except HTTPException as e:
        if e.status_code == 404:
            raise HTTPException(status_code=404, detail="Message not found")
        if e.status_code == 304:
            print(f"Message rating already updated")
            raise HTTPException(
                status_code=304,
                detail="Message rating already updated",
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to update message rating: {e.detail}",
            )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update message rating: {e}",
        )
