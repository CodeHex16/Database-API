from typing import List

from fastapi import BackgroundTasks, FastAPI
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from pydantic import BaseModel, EmailStr
from starlette.responses import JSONResponse
from dotenv import load_dotenv
import os

load_dotenv() 


class EmailService:
    def __init__(self):
        self.conf = ConnectionConfig(
            MAIL_USERNAME=os.getenv("MAIL_ADDRESS"),
            MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
            MAIL_FROM=os.getenv("MAIL_ADDRESS"),
            MAIL_FROM_NAME=os.getenv("MAIL_USERNAME"),
            MAIL_PORT=int(os.getenv("MAIL_PORT")),
            MAIL_SERVER=os.getenv("MAIL_SERVER"),
            MAIL_STARTTLS = True,
            MAIL_SSL_TLS = False,            
            USE_CREDENTIALS=True,
            VALIDATE_CERTS=True,
        )
        self.mail = FastMail(self.conf)

    async def send_email(self, to: List[EmailStr], subject: str, body: str):
        message = MessageSchema(
            subject=subject, recipients=to, body=body, subtype=MessageType.plain #or MessageType.html        
        )
        await self.mail.send_message(message)
