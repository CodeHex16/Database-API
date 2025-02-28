from pydantic import BaseModel, EmailStr, UUID4, Field, field_validator
from typing import Union, Optional, List
from datetime import datetime


class UserRegister(BaseModel):
    email: EmailStr
    password: str

    @field_validator("password")
    def check_password(value: str):
        if len(value) < 8:
            raise ValueError("La password deve essere lunga almeno 8 caratteri")
        return value


class UserDB(BaseModel):
    email: EmailStr
    hashed_password: str
    is_initialized: bool


class Token(BaseModel):
    access_token: str
    token_type: str


class ChatResponse(BaseModel):
    id: str
    name: str
    user_email: str
    created_at: Optional[datetime] = None


class ChatList(BaseModel):
    chats: List[ChatResponse]


class Message(BaseModel):
    sender: EmailStr
    content: str
    timestamp: datetime


class ChatMessages(BaseModel):
    name: str
    messages: List[Message]


class MessageCreate(BaseModel):
    content: str
