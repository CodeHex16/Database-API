from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from typing import List, Optional
from datetime import datetime
from pydantic import EmailStr
import requests

from ..database import get_db
from ..repositories.chat_repository import ChatRepository
from .. import schemas
from .auth import verify_token, oauth2_scheme
from typing_extensions import Annotated

router = APIRouter(
    prefix="/chats",
    tags=["chats"],
)


def get_chat_repository(db=Depends(get_db)):
    return ChatRepository(db)


@router.get("", response_model=List[schemas.ChatResponse])
async def get_chats(
    token: Annotated[str, Depends(oauth2_scheme)],
    chat_repository=Depends(get_chat_repository),
):
    # Verifica il token e ottieni l'email dell'utente
    payload = verify_token(token=token)
    user_email = payload.get("sub")

    if not user_email:
        raise HTTPException(status_code=400, detail="Invalid user information in token")

    chats = await chat_repository.get_by_user_email(user_email)

    result = []

    for chat in chats:
        result.append(
            {
                "id": str(chat["_id"]),
                "name": chat.get("name", "Chat senza nome"),
                "user_email": chat["user_email"],
                "created_at": chat.get("created_at"),
            }
        )

    return result


@router.put("/{chat_id}", response_model=schemas.ChatResponse)
async def update_chat(
    chat_id: str,
    chat: str,  # TODO: Fix this
    token: Annotated[str, Depends(oauth2_scheme)],
    chat_repository=Depends(get_chat_repository),
):
    payload = verify_token(token=token)
    user_email = payload.get("sub")

    # Verifica che la chat esista e appartenga all'utente
    existing_chat = await chat_repository.get_by_id(chat_id, user_email)
    if not existing_chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    # Aggiorna solo i campi che sono stati forniti
    update_data = {}
    if chat.name is not None:
        update_data["name"] = chat.name

    if update_data:
        await chat_repository.update(chat_id, update_data)

    # Recupera la chat aggiornata
    updated_chat = await chat_repository.get_by_id(chat_id, user_email)

    return {
        "id": str(updated_chat["_id"]),
        "name": updated_chat["name"],
        "user_email": updated_chat["user_email"],
        "created_at": updated_chat.get("created_at"),
    }


@router.delete("/{chat_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chat(
    chat_id: str,
    token: Annotated[str, Depends(oauth2_scheme)],
    chat_repository=Depends(get_chat_repository),
):
    payload = verify_token(token=token)
    user_email = payload.get("sub")

    # Verifica che la chat esista e appartenga all'utente
    existing_chat = await chat_repository.get_by_id(chat_id, user_email)
    if not existing_chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    await chat_repository.delete(chat_id, user_email)
    return None


@router.get("/{chat_id}/messages", response_model=schemas.ChatMessages)
async def get_chat_messages(
    chat_id: str,
    token: Annotated[str, Depends(oauth2_scheme)],
    chat_repository=Depends(get_chat_repository),
):
    payload = verify_token(token=token)
    user_email = payload.get("sub")

    # Verifica che la chat esista e appartenga all'utente
    existing_chat = await chat_repository.get_by_id(chat_id, user_email)
    if not existing_chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    result = {
        "name": existing_chat.get("name"),
        "messages": existing_chat.get("messages"),
    }

    return result


@router.post("/{chat_id}/messages", response_model=schemas.Message)
async def create_chat_message(
    chat_id: str,
    message: schemas.MessageCreate,
    token: Annotated[str, Depends(oauth2_scheme)],
    background_tasks: BackgroundTasks,
    chat_repository=Depends(get_chat_repository),
):
    payload = verify_token(token=token)
    user_email = payload.get("sub")

    # Verifica che la chat esista e appartenga all'utente
    existing_chat = await chat_repository.get_by_id(chat_id, user_email)
    if not existing_chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    message_data = {
        "sender": "user",
        "content": message.content,
        "timestamp": datetime.now(),
    }

    # Aggiungi il messaggio alla chat
    existing_chat["messages"].append(message_data)

    await chat_repository.update(chat_id, {"messages": existing_chat["messages"]}) # aggiorna nel DB

    print("Sending message to AI model START")

    background_tasks.add_task(
        process_ai_response,
        chat_id,
        user_email,
        message_data["content"],
        chat_repository,
    )

    print("Recive message to AI model END")

    return message_data


async def process_ai_response(
    chat_id: str, user_email: EmailStr, message: str, chat_repository: ChatRepository
):
    chat = await chat_repository.get_by_id(
        chat_id,
        user_email,
    )
    if not chat:
        return
    
    print("Sending message to AI model BACKGROUND TASK")

    res = requests.post("http://localhost:8001/", json={"question": message})
    risposta = res.json()["answer"]

    risposta_data = {
        "sender": "bot",
        "content": risposta,
        "timestamp": datetime.now(),
    }

    chat["messages"].append(risposta_data)
    await chat_repository.update(chat_id, {"messages": chat["messages"]}) 

    print("Returning response from AI model BACKGROUND TASK")
    return risposta_data


@router.get("/new_chat")  # response_model=List[schemas.ChatResponse]
async def get_new_chat(
    token: Annotated[str, Depends(oauth2_scheme)],
    chat_repository=Depends(get_chat_repository),
):
    payload = verify_token(token=token)
    user_email = payload.get("sub")

    if not user_email:
        raise HTTPException(status_code=400, detail="Invalid user information in token")

    chats = await chat_repository.initialize_chat(user_email)

    return {"chat_id": str(chats["_id"])}
