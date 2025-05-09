from pymongo.errors import DuplicateKeyError
from datetime import datetime
from pydantic import EmailStr
from bson import ObjectId

from app.utils import get_timezone, get_object_id
import app.schemas as schemas
from motor.motor_asyncio import AsyncIOMotorDatabase
from fastapi import Depends
from app.database import get_db

class DocumentRepository:
    def __init__(self, database):
        self.database = database
        self.collection = database.get_collection("documents")

    async def get_documents(self):
        return await self.collection.find().to_list(length=None)

    async def insert_document(self, owner_email: EmailStr, document: schemas.Document):
        """
        Inserisce un nuovo documento nel database.
        Il documento viene memorizzato con un ObjectId generato dal suo percorso file come chiave primaria.
        """
        document_data = {
            "_id": get_object_id(document.file_path),
            "title": document.title,
            "file_path": document.file_path,
            "owner_email": owner_email,
            "uploaded_at": datetime.now(get_timezone()).isoformat(),
        }
        try:
            return await self.collection.insert_one(document_data)
        except DuplicateKeyError as e:
            print(f"Error inserting document: {e}.")
            raise DuplicateKeyError(f"Error inserting document: {e}.")
        except Exception as e:
            print(f"Error inserting document: {e}")
            raise Exception(f"Error inserting document: {e}")

    async def delete_document(self, file_id: ObjectId):
        """
        Elimina un documento dal database in base all'ObjectId passato come file_id.
        """
        try:
            print(f"Sto cancellando il documento da MongoDB {file_id}")
            return await self.collection.delete_one({"_id": file_id})
        except Exception as e:
            print(f"Error deleting document: {e}")
            raise Exception(f"Error deleting document: {e}")

def get_document_repository(db: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Restituisce un'istanza del repository dei documenti.

    Args:
        db (AsyncIOMotorDatabase): Il database MongoDB.

    Returns:
        DocumentRepository: Un'istanza del repository dei documenti.
    """
    return DocumentRepository(db)
