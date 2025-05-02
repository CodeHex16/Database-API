from pydantic import BaseModel, EmailStr, UUID3, Field, field_validator
from bson import ObjectId
from typing import Union, Optional, List, Annotated, Any, Callable
from datetime import datetime
from pydantic_core import core_schema
import re


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
            return ObjectId()

        return core_schema.union_schema(
            [
                # check if it's an instance first before doing any further work
                core_schema.is_instance_schema(ObjectId),
                core_schema.no_info_plain_validator_function(validate_from_str),
            ],
            serialization=core_schema.to_string_ser_schema(),
        )


PydanticObjectId = Annotated[ObjectId, _ObjectIdPydanticAnnotation]

# Define the regex pattern as a constant
PASSWORD_REGEX = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^a-zA-Z0-9]).{8,}$"
PASSWORD_ERROR_MSG = "La password deve contenere almeno 8 caratteri, una lettera maiuscola, una lettera maiuscola, una cifra e un carattere speciale."


class User(BaseModel):
    id: EmailStr = Field(alias="_id")
    name: str
    hashed_password: str
    is_initialized: bool = False
    remember_me: bool = False
    scopes: List[str] = ["user"]


class UserAuth(BaseModel):
    email: EmailStr
    password: str

    @field_validator("password")
    def check_password_complexity(cls, value: str):
        if not re.match(PASSWORD_REGEX, value):
            raise ValueError(PASSWORD_ERROR_MSG)
        return value


class UserUpdatePassword(BaseModel):
    password: str
    current_password: str

    @field_validator("password")
    def check_password_complexity(cls, value: str):
        if not re.match(PASSWORD_REGEX, value):
            raise ValueError(PASSWORD_ERROR_MSG)
        return value


class UserUpdate(BaseModel):
    password: Optional[str] = None
    is_initialized: Optional[bool] = None
    remember_me: Optional[bool] = None
    scopes: Optional[List[str]] = None

    @field_validator("password")
    def check_optional_password_complexity(cls, value: Optional[str]):
        if value is not None:
            if not re.match(PASSWORD_REGEX, value):
                raise ValueError(PASSWORD_ERROR_MSG)
        return value

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    scopes: Optional[List[str]] = None

class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: Optional[int] = None


class ChatResponse(BaseModel):
    id: str
    name: str
    user_email: EmailStr
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
    # id: PydanticObjectId = Field(alias="_id")
    title: str
    question: str
    answer: str

    @field_validator("title")
    def check_title_length(cls, value: str):
        if len(value) > 20:
            raise ValueError(f"Il titolo deve essere lungo massimo 20 caratteri")
        return value

    model_config = {
        "populate_by_name": True,  # Allows using '_id' in input data
        "json_encoders": {ObjectId: str},  # Ensure ObjectId is serialized as string
    }


class FAQUpdate(BaseModel):
    title: Optional[str]
    question: Optional[str]
    answer: Optional[str]

    @field_validator("title")
    def check_title_length(cls, value: Optional[str]):
        if len(value) > 20:
            raise ValueError(f"Il titolo deve essere lungo massimo 20 caratteri")
        return value


class EmailSchema(BaseModel):
    email: List[EmailStr]