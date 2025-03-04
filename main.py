from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from logging import info

import os
from dotenv import load_dotenv

from .database import init_db, get_db

from .routes import auth, chat

load_dotenv()

# Ottieni l'URL del MongoDB dall'ambiente
MONGODB_URL = os.getenv("MONGODB_URL")


async def lifespan(app: FastAPI):
    # Startup
    app.mongodb_client = AsyncIOMotorClient(MONGODB_URL)
    app.database = app.mongodb_client.get_default_database()
    info("Connected to the MongoDB database!")
    init_db(app.database)

    yield

    # Shutdown
    app.mongodb_client.close()
    info("Disconnected from the MongoDB database")


app = FastAPI(
    lifespan=lifespan,
    title="Suppl-AI API",
    description="API for the Suppl-AI project",
    version="0.2",
)

origins = ["http://localhost:3001", "http://localhost:8000"
           "http://192.168.1.44:3001", "http://192.168.1.44:8000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

auth.init_router(app)
app.include_router(auth.router)
app.include_router(chat.router)
