import os
from fastapi import Depends
from motor.motor_asyncio import AsyncIOMotorClient


MONGODB_URL = os.getenv("MONGODB_URL")

# Utilizziamo una variabile globale per memorizzare l'app
_app = None


def set_app(app):
    global _app
    _app = app


async def get_db():
    global _app
    if _app is None:
        # Durante l'inizializzazione, l'app potrebbe non essere ancora impostata
        from main import app

        _app = app

    return _app.database
