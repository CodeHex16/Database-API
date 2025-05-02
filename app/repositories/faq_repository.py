from bson import ObjectId
from pymongo.errors import DuplicateKeyError
from datetime import datetime
from fastapi import HTTPException, status

import app.schemas as schemas
from app.utils import get_timezone

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

    async def insert_faq(self, faq: schemas.FAQ, author_email: str):
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
        try:
            insert_payload = {
                "title": faq.title,
                "question": faq.question,
                "answer": faq.answer,
                "author_email": author_email,
                "created_at": datetime.now(get_timezone()).isoformat(),
                "updated_at": datetime.now(get_timezone()).isoformat(),
            }
            result = await self.collection.insert_one(insert_payload)
            return result.inserted_id
        except DuplicateKeyError as e:
            print(f"Error inserting FAQ: {e}.")
            raise DuplicateKeyError(f"Error inserting FAQ: {e}.")
        except Exception as e:
            print(f"Error inserting FAQ: {e}")
            raise Exception(f"Error inserting FAQ: {e}")

    async def update_faq(
        self, faq_id: ObjectId, faq_data: schemas.FAQUpdate, author_email: str
    ):
        """
        Aggiorna una FAQ esistente nel database.

        Args:
            faq (schemas.FAQ): L'oggetto FAQ da aggiornare.

        Returns:
            Il risultato dell'operazione di aggiornamento.
        """
        try:
            # print(f"Updating FAQ: {faq}")

            # Ottiene i dati della FAQ esistente
            faq_current_data = await self.get_faq_by_id(faq_id)

            # Controla se la FAQ esiste
            if not faq_current_data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="FAQ not found",
                )

            # Controlla se sono cambiati i dati
            if (
                faq_current_data.get("title") == faq_data.title
                and faq_current_data.get("question") == faq_data.question
                and faq_current_data.get("answer") == faq_data.answer
            ):
                print("FAQ data is already up to date.")
                raise HTTPException(
                    status_code=status.HTTP_304_NOT_MODIFIED,
                    detail="FAQ data is already up to date.",
                )

            # Prepara il payload di aggiornamento
            update_payload = {
                "title": (
                    faq_data.title if faq_data.title else faq_current_data.get("title")
                ),
                "question": (
                    faq_data.question
                    if faq_data.question
                    else faq_current_data.get("question")
                ),
                "answer": (
                    faq_data.answer
                    if faq_data.answer
                    else faq_current_data.get("answer")
                ),
                "author_email": author_email,
                "updated_at": datetime.now(get_timezone()).isoformat(),
            }

            # Esegue l'aggiornamento
            result = await self.collection.update_one(
                {"_id": faq_id},
                {"$set": update_payload},
            )

            # Controlla se l'aggiornamento ha avuto effetto
            if result.matched_count == 0:
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
            # print(f"Deleting FAQ with ID: {faq_id}")
            return await self.collection.delete_one({"_id": faq_id})
        except Exception as e:
            print(f"Error deleting FAQ: {e}")
            raise Exception(f"Error deleting FAQ: {e}")
