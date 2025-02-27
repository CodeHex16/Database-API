from typing import Union, Optional
from typing_extensions import Annotated
from fastapi import FastAPI, Depends, HTTPException, status
from datetime import datetime, timedelta, timezone
from pydantic import BaseModel, EmailStr, Field
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
from motor.motor_asyncio import AsyncIOMotorClient
from contextlib import asynccontextmanager
from logging import info
from jose import JWTError, jwt

import os
from dotenv import load_dotenv

from . import schemas
from .database import get_db
from .repositories.user_repository import UserRepository

from .routes import auth, chat

load_dotenv()

# Ottieni l'URL del MongoDB dall'ambiente
MONGODB_URL = os.getenv("MONGODB_URL")


async def lifespan(app: FastAPI):
    # Startup
    app.mongodb_client = AsyncIOMotorClient(MONGODB_URL)
    app.database = app.mongodb_client.get_default_database()
    info("Connected to the MongoDB database!")

    yield

    # Shutdown
    app.mongodb_client.close()
    info("Disconnected from the MongoDB database")


app = FastAPI(
    lifespan=lifespan,
    title="Suppl-AI MongoDB API",
    description="This is the API for the Suppl-AI MongoDB project",
    version="0.1",
)

origins = ["http://localhost:3001", "http://localhost:8000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Aggiungi:
print("App:", app)
print("Auth module:", auth)
print("Init router exists:", hasattr(auth, "init_router"))

# Passa il database al router di autenticazione
auth.init_router(app)
app.include_router(auth.router)
app.include_router(chat.router)