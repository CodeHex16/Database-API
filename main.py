from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from logging import info

import os
from dotenv import load_dotenv

from database import init_db, get_db

from routes import auth, chat
from repositories.user_repository import UserRepository

load_dotenv()

# Ottieni l'URL del MongoDB dall'ambiente
MONGODB_URL = os.getenv("MONGODB_URL")


async def lifespan(app: FastAPI):
    # Startup
    app.mongodb_client = AsyncIOMotorClient(MONGODB_URL+"/supplai?authSource=admin")
    app.database = app.mongodb_client.get_default_database()
    info("Connected to the MongoDB database!")
    init_db(app.database)
    
	# TODO: da rimuovere
    # AGGIUNGI UTENTE TEST
    user_repo = UserRepository(app.database)
    test_user = await user_repo.get_test_user()
    if not test_user:
        await user_repo.add_test_user()
        print("Utente test aggiunto con successo")
    else:
        print("Utente test già presente nel database")

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

origins = [
    "http://suppl-ai:3000",
    "http://database-api:8000",
    "http://localhost:3000",
    "http://localhost:8000",
    "http://localhost:8001",
]

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

    