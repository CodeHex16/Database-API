from pydantic import BaseModel, EmailStr, UUID4, Field
from typing import Union, Optional

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