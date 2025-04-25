from bson import ObjectId
from pymongo.errors import DuplicateKeyError
from datetime import datetime

import app.schemas as schemas

class FaqRepository:
    def __init__(self, database):
        self.database = database
        self.collection = database.get_collection("faq")

    async def get_faqs(self):
        """
        Restituisce una lista di tutte le FAQ.
        """
        return await self.collection.find().to_list(length=None)

    async def insert_faq(self, faq: schemas.FAQ):
        """
        Inserisce una nuova FAQ nel database.
        La FAQ viene memorizzata con un UUID generato dal suo percorso file come chiave primaria.

        Args:
            faq (schemas.FAQ): L'oggetto FAQ da inserire.

        Returns:
            Il risultato dell'operazione di inserimento.

        Raises:
            DuplicateKeyError: Se una FAQ con lo stesso percorso esiste già.
            Exception: Se si verifica qualsiasi altro errore durante l'inserimento.
        """
        faq_data = {
            "_id": ObjectId(),
            "title": faq.title,
            "question": faq.question,
            "answer": faq.answer,
            "created_at": datetime.now(),
        }
        try:
            return await self.collection.insert_one(faq_data)
        except DuplicateKeyError as e:
            print(f"Error inserting FAQ: {e}.")
            raise DuplicateKeyError(f"Error inserting FAQ: {e}.")
        except Exception as e:
            print(f"Error inserting FAQ: {e}")
            raise Exception(f"Error inserting FAQ: {e}")
