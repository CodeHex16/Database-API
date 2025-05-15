from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from logging import info

import os
from dotenv import load_dotenv

from app.database import init_db, get_db, MONGODB_URL

from app.routes import auth, chat, document, user, faq, setting
from app.repositories.user_repository import UserRepository

load_dotenv()

async def lifespan(app: FastAPI):
    # Startup
    app.mongodb_client = AsyncIOMotorClient(MONGODB_URL + "/supplai?authSource=admin")
    app.database = app.mongodb_client.get_default_database()

    if not app.database:
        raise Exception("Database connection failed")
    
    if not app.mongodb_client:
        raise Exception("MongoDB client connection failed")
    
    info("Connected to the MongoDB database!")
    init_db(app.database)

    user_repo = UserRepository(app.database)
    if os.getenv("ENVIRONMENT") == "development":
        # AGGIUNGI UTENTE TEST (Solo in sviluppo)
        test_user = await user_repo.get_test_user()
        if not test_user:
            await user_repo.add_test_user()
            print("Utente test aggiunto con successo")
        else:
            print("Utente test già presente nel database")
    
    if (not os.getenv("ADMIN_EMAIL")) or (not os.getenv("ADMIN_PASSWORD")):
        print("ADMIN_EMAIL e ADMIN_PASSWORD non sono stati definiti in .env")
        print("Defalt admin user:", os.getenv("ADMIN_EMAIL") or "admin@test.it")
        print("Defalt admin password:", os.getenv("ADMIN_PASSWORD") or "adminadmin")

    admin_user = await user_repo.get_by_email(os.getenv("ADMIN_EMAIL") or "admin@test.it")
    if not admin_user:
        await user_repo.add_test_admin()
        print("Utente admin aggiunto con successo")
    else:
        print("Utente admin già presente nel database")
        
    yield

    # Shutdown
    app.mongodb_client.close()
    info("Disconnected from the MongoDB database")


app = FastAPI(
    lifespan=lifespan,
    title="Database-AI API",
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

app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(document.router)
app.include_router(user.router)
app.include_router(faq.router)
app.include_router(setting.router)
