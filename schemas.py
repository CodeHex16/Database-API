from pydantic import BaseModel, EmailStr, UUID4, Field
from typing import Union, Optional, List
from datetime import datetime


class UserRegister(BaseModel):
    email: EmailStr
    password: str


class UserDB(BaseModel):
    email: EmailStr
    hashed_password: str
    is_initialized: bool


class Token(BaseModel):
    access_token: str
    token_type: str


class ChatCreate(BaseModel):
    name: str = "Nuova chat"


class ChatUpdate(BaseModel):
    name: Optional[str] = None


class ChatResponse(BaseModel):
    id: str
    name: str
    user_email: str
    created_at: Optional[datetime] = None


class ChatList(BaseModel):
    chats: List[ChatResponse]

class MessageCreate(BaseModel):
    chat_id: str
    content: str
     