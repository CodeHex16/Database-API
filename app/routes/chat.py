import os
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from typing import List, Optional
from datetime import datetime
from pydantic import EmailStr
import requests

from app.database import get_db
from app.repositories.chat_repository import ChatRepository
import app.schemas as schemas
from app.routes.auth import (
    verify_token,
    oauth2_scheme,
    verify_user,
    verify_admin,
)
from typing_extensions import Annotated

router = APIRouter(
    prefix="/chats",
    tags=["chats"],
)


def get_chat_repository(db=Depends(get_db)):
    return ChatRepository(db)


@router.get("", response_model=List[schemas.ChatResponse])
async def get_chats(
    current_user=Depends(verify_user),
    chat_repository=Depends(get_chat_repository),
):
    # Verifica il token e ottieni l'email dell'utente
    user_email = current_user.get("sub")

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
    current_user=Depends(verify_user),
    chat_repository=Depends(get_chat_repository),
):
    user_email = current_user.get("sub")

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
    current_user=Depends(verify_user),
    chat_repository=Depends(get_chat_repository),
):
    user_email = current_user.get("sub")

    # Verifica che la chat esista e appartenga all'utente
    existing_chat = await chat_repository.get_by_id(chat_id, user_email)
    if not existing_chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    await chat_repository.delete(chat_id, user_email)
    return None


@router.get("/{chat_id}/messages", response_model=schemas.ChatMessages)
async def get_chat_messages(
    chat_id: str,
    current_user=Depends(verify_user),
    chat_repository=Depends(get_chat_repository),
):

    user_email = current_user.get("sub")

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
    current_user=Depends(verify_user),
    chat_repository=Depends(get_chat_repository),
):
    user_email = current_user.get("sub")

    # Verifica che la chat esista e appartenga all'utente
    existing_chat = await chat_repository.get_by_id(chat_id, user_email)
    if not existing_chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    message_data = {
        "sender": message.sender,
        "content": message.content,
        "timestamp": datetime.now(),
    }

    # Aggiungi il messaggio alla chat
    existing_chat["messages"].append(message_data)

    await chat_repository.update(
        chat_id, {"messages": existing_chat["messages"]}
    )  # aggiorna nel DB

    return message_data


@router.get("/new_chat")  # response_model=List[schemas.ChatResponse]
async def get_new_chat(
    current_user=Depends(verify_user),
    chat_repository=Depends(get_chat_repository),
):
    user_email = current_user.get("sub")

    if not user_email:
        raise HTTPException(status_code=400, detail="Invalid user information in token")

    chats = await chat_repository.initialize_chat(user_email)

    return {"chat_id": str(chats["_id"])}


@router.put("/{chat_id}/name")
async def change_chat_name(
    chat_id: str,
    new_name: str,
    current_user=Depends(verify_user),
    chat_repository=Depends(get_chat_repository),
):
    user_email = current_user.get("sub")

    # Verifica che la chat esista e appartenga all'utente
    existing_chat = await chat_repository.get_by_id(chat_id, user_email)
    if not existing_chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    await chat_repository.update(chat_id, {"name": new_name})

    return {"message": "Chat name updated successfully"}
