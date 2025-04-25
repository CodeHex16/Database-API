from pydantic import BaseModel, EmailStr, UUID3, Field, field_validator
from bson import ObjectId
from typing import Union, Optional, List, Annotated, Any, Callable
from datetime import datetime
from pydantic_core import core_schema


# Implementazione ObjectId per pydantic
class _ObjectIdPydanticAnnotation:
    # Based on https://docs.pydantic.dev/latest/usage/types/custom/#handling-third-party-types.

    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        _source_type: Any,
        _handler: Callable[[Any], core_schema.CoreSchema],
    ) -> core_schema.CoreSchema:
        def validate_from_str(input_value: str) -> ObjectId:
            return ObjectId(input_value)

        return core_schema.union_schema(
            [
                # check if it's an instance first before doing any further work
                core_schema.is_instance_schema(ObjectId),
                core_schema.no_info_plain_validator_function(validate_from_str),
            ],
            serialization=core_schema.to_string_ser_schema(),
        )

PydanticObjectId = Annotated[ObjectId, _ObjectIdPydanticAnnotation]


class User(BaseModel):
    # id: UUID3 = Field(default_factory=UUID3, alias="_id")
    # email: EmailStr
    id: EmailStr
    hashed_password: str
    is_initialized: bool = False
    remember_me: bool = False
    scopes: List[str] = ["user"]


class UserAuth(BaseModel):
    email: EmailStr
    password: str

    @field_validator("password")
    def check_password(value: str):
        if len(value) < 8:
            raise ValueError("La password deve essere lunga almeno 8 caratteri")
        return value


class UserChangePassword(UserAuth):
    current_password: str


class UserUpdate(BaseModel):
    id: EmailStr
    hashed_password: str | None
    is_initialized: bool | None
    remember_me: bool | None
    scopes: List[str] | None

    @field_validator("hashed_password")
    def check_password(value: str):
        if len(value) < 8:
            raise ValueError("La password deve essere lunga almeno 8 caratteri")
        return value


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
    id: PydanticObjectId = Field(alias='_id')
    title: str
    question: str
    answer: str
    author_email: EmailStr