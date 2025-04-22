from pydantic import BaseModel, EmailStr, UUID3, Field, field_validator
from typing import Union, Optional, List
from datetime import datetime


class UserEmailPwd(BaseModel):
    email: EmailStr
    password: str

    @field_validator("password")
    def check_password(value: str):
        if len(value) < 8:
            raise ValueError("La password deve essere lunga almeno 8 caratteri")
        return value


class User(BaseModel):
    # id: UUID3 = Field(default_factory=UUID3, alias="_id")
    # email: EmailStr
    _id: EmailStr
    hashed_password: str
    is_initialized: bool = False
    remember_me: bool = False
    scopes: List[str] = ["user"]


class UserNewData(BaseModel):
    id: EmailStr
    hashed_password: str | None
    is_initialized: bool | None
    remember_me: bool | None
    scopes: List[str] | None


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
    sender: str
    content: str
    timestamp: datetime


class ChatMessages(BaseModel):
    name: str
    messages: List[Message]


class MessageCreate(BaseModel):
    content: str
    sender: str = "user"


class Document(BaseModel):
    title: str
    file_path: str
    owner_email: str
    uploaded_at: datetime


class FAQ(BaseModel):
    short_question: str
    question: str
    answer: str
    author_email: EmailStr
