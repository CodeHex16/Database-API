import os
import regex


MONGODB_URL = os.getenv("MONGODB_URL")
MONGO_USERNAME = os.getenv("MONGO_USERNAME")
MONGO_PASSWORD = os.getenv("MONGO_PASSWORD")

# Se l'MONGODB_URL se contiene username e password, allora usa MONGODB_URL
if MONGODB_URL and regex.match(r"^mongodb://.*:.*@.*:.*", MONGODB_URL):
    MONGODB_URL = MONGODB_URL
# Se l'MONGODB_URL non contiene username e password, allora usa MONGO_USERNAME e MONGO_PASSWORD
elif MONGO_USERNAME and MONGO_PASSWORD and regex.match(r"^.*:.*", MONGODB_URL):
    MONGODB_URL = f"mongodb://{MONGO_USERNAME}:{MONGO_PASSWORD}@{MONGODB_URL}"
else:
    # Se non sono presenti username e password, usa l'URL di default
    MONGODB_URL = "mongodb://root:example@localhost:27017"



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