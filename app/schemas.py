from pydantic import BaseModel, EmailStr, Field, field_validator
from bson import ObjectId
from typing import Optional, List, Annotated, Any, Callable
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
    current_password: str


class UserForgotPassword(BaseModel):
    email: EmailStr


class UserUpdatePassword(BaseModel):
    password: str
    current_password: str

    @field_validator("password")
    def check_password_complexity(cls, value: str):
        if not re.match(PASSWORD_REGEX, value):
            raise ValueError(PASSWORD_ERROR_MSG)
        return value


class UserUpdate(BaseModel):
    id: Optional[EmailStr] = Field(alias="_id")
    name: Optional[str] = None
    password: Optional[str] = None
    is_initialized: Optional[bool] = None
    remember_me: Optional[bool] = None
    scopes: Optional[List[str]] = None


class UserDelete(BaseModel):
    id: EmailStr = Field(alias="_id")


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
    created_at: Optional[str] = None


class ChatList(BaseModel):
    chats: List[ChatResponse]


class Message(BaseModel):
    id: PydanticObjectId = Field(alias="_id")
    sender: str
    content: str
    timestamp: str
    rating: Optional[bool]


class ChatMessages(BaseModel):
    name: str
    messages: List[Message]


class MessageCreate(BaseModel):
    content: str
    sender: str = "user"
    rating: Optional[bool] = None


class MessageRatingUpdate(BaseModel):
    rating: Optional[bool] = None


class Document(BaseModel):
    title: str
    file_path: str


class DocumentResponse(Document):
    id: PydanticObjectId = Field(alias="_id")
    owner_email: EmailStr
    uploaded_at: str

class DocumentDelete(BaseModel):
    id: str

class FAQ(BaseModel):
    # id: PydanticObjectId = Field(alias="_id")
    title: str
    question: str
    answer: str

    @field_validator("title")
    def check_title_length(cls, value: str):
        if len(value) > 30:
            raise ValueError(f"Il titolo deve essere lungo massimo 30 caratteri")
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


class FAQResponse(FAQ):
    id: PydanticObjectId = Field(alias="_id")
    created_at: str
    updated_at: str


class EmailSchema(BaseModel):
    email: List[EmailStr]
