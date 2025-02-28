import os
from motor.motor_asyncio import AsyncIOMotorClient

MONGODB_URL = os.getenv("MONGODB_URL")

# Variabile globale per memorizzare la connessione al database
_db = None


def init_db(db_instance):
    """Inizializza la connessione al database"""
    global _db
    _db = db_instance


async def get_db():
    """Restituisce l'istanza del database"""
    global _db
    if _db is None:
        # Se il database non è stato inizializzato, solleva un'eccezione
        raise RuntimeError(
            "Database non inizializzato. Chiamare init_db() prima dell'utilizzo."
        )
    return _db
