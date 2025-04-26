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

    async def get_faq_by_id(self, faq_id: ObjectId):
        """
                Restituisce una FAQ specifica in base all'ID fornito.

                Args:
                    faq_id (ObjectId): L'ID della FAQ da recuperare.

                Returns:
                    La FAQ corrispondente all'ID fornito.

                Raises:
                    Exception: Se si verifica un errore durante il recupero della FAQ.
        """
        try:
            return await self.collection.find_one({"_id": faq_id})
        except Exception as e:
            print(f"Error retrieving FAQ: {e}")
            raise Exception(f"Error retrieving FAQ: {e}")

    async def insert_faq(self, faq: schemas.FAQ):
        """
        Inserisce una nuova FAQ nel database.
        L'ID viene generato automaticamente da MongoDB.

        Args:
            faq (schemas.FAQ): L'oggetto FAQ da inserire.

        Returns:
            ObjectId: L'ID del documento inserito.

        Raises:
            DuplicateKeyError: Se si verifica un errore di chiave duplicata.
            Exception: Se si verifica qualsiasi altro errore durante l'inserimento.
        """
        faq_data = {
            "title": faq.title,
            "question": faq.question,
            "answer": faq.answer,
            "author_email": faq.author_email,
            "created_at": faq.created_at,
            "updated_at": faq.updated_at,
        }
        try:
            result = await self.collection.insert_one(faq_data)
            return result.inserted_id
        except DuplicateKeyError as e:
            print(f"Error inserting FAQ: {e}.")
            raise DuplicateKeyError(f"Error inserting FAQ: {e}.")
        except Exception as e:
            print(f"Error inserting FAQ: {e}")
            raise Exception(f"Error inserting FAQ: {e}")

    async def update_faq(self, faq: schemas.FAQUpdate):
        """
        Aggiorna una FAQ esistente nel database.

        Args:
            faq (schemas.FAQ): L'oggetto FAQ da aggiornare.

        Returns:
            Il risultato dell'operazione di aggiornamento.
        """
        try:
            # print(f"Updating FAQ: {faq}")
            result = await self.collection.update_one(
                {"_id": faq.get("id")},
                {
                    "$set": {
                        "title": faq.get("title"),
                        "question": faq.get("question"),
                        "answer": faq.get("answer"),
                        "author_email": faq.get("author_email"),
                        "updated_at": faq.get("updated_at"),
                    }
                },
            )

            if result.modified_count == 0 and result.matched_count > 0:
                print("FAQ data is already up to date.")
                return {"message": "FAQ data is already up to date."}
            elif result.matched_count == 0:
                print("FAQ not found during update attempt")
                raise Exception("FAQ not found during update attempt")
        except Exception as e:
            print(f"Error updating FAQ: {e}")
            raise Exception(f"Error updating FAQ: {e}")

    async def delete_faq(self, faq_id: ObjectId):
        """
        Elimina una FAQ dal database.

        Args:
            faq_id (ObjectId): L'ID della FAQ da eliminare.

        Returns:
            Il risultato dell'operazione di eliminazione.
        """
        try:
            print(f"Deleting FAQ with ID: {faq_id}")
            return await self.collection.delete_one({"_id": faq_id})
        except Exception as e:
            print(f"Error deleting FAQ: {e}")
            raise Exception(f"Error deleting FAQ: {e}")
