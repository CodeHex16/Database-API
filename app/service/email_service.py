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
            MAIL_USERNAME=os.getenv("MAIL_ADDRESS",""),
            MAIL_PASSWORD=os.getenv("MAIL_PASSWORD",""),
            MAIL_FROM=os.getenv("MAIL_ADDRESS","test@test.com"),
            MAIL_FROM_NAME=os.getenv("MAIL_USERNAME",""),
            MAIL_PORT=os.getenv("MAIL_PORT",587),
            MAIL_SERVER=os.getenv("MAIL_SERVER",""),
            MAIL_STARTTLS = os.getenv("MAIL_STARTTLS",True),
            MAIL_SSL_TLS = os.getenv("MAIL_USE_CREDENTIALS", False),
            USE_CREDENTIALS=os.getenv("USE_CREDENTIALS",True),
            VALIDATE_CERTS=os.getenv("VALIDATE_CERTS",True),
        )
        self.mail = FastMail(self.conf)

    async def send_email(self, to: List[EmailStr], subject: str, body: str):
        if not self.is_configuration_valid():
          raise ValueError("Email configuration is not valid. Please check your environment variables.")
        else:
            message = MessageSchema(
                subject=subject, recipients=to, body=body, subtype=MessageType.plain #or MessageType.html        
            )
            await self.mail.send_message(message)
    
    def is_configuration_valid(self):
        return all([
            self.conf.MAIL_USERNAME,
            self.conf.MAIL_PASSWORD,
            self.conf.MAIL_FROM,
            self.conf.MAIL_PORT,
            self.conf.MAIL_SERVER,
            self.conf.MAIL_STARTTLS,
            self.conf.MAIL_SSL_TLS,
            self.conf.USE_CREDENTIALS,
            self.conf.VALIDATE_CERTS
        ])
