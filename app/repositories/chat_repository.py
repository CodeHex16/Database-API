from bson import ObjectId
from datetime import datetime

from app.utils import get_timezone
import app.schemas as schemas

from app.database import get_db
from fastapi import Depends


class ChatRepository:
    def __init__(self, database):
        self.database = database
        self.collection = database.get_collection("chats")

    async def get_chat_by_user_email(self, user_email, limit=100):
        return await self.collection.find({"user_email": user_email}).to_list(
            length=limit
        )

    async def get_chat_by_id(self, chat_id, user_email):
        return await self.collection.find_one(
            {"_id": ObjectId(chat_id), "user_email": user_email}
        )

    async def initialize_chat(self, user_email):
        """Inizializza una nuova chat con il messaggio iniziale del bot"""

        chat_data = {
            "name": "Chat senza nome",
            "user_email": user_email,
            "created_at": datetime.now(get_timezone()).isoformat(),
            "messages": [
                {
                    "_id": ObjectId(),
                    "sender": "bot",
                    "content": "Ciao, sono SupplAI, il tuo assistente per gli acquisti personale! Come posso aiutarti?",
                    "timestamp": datetime.now(get_timezone()).isoformat(),
                    "rating": None,
                }
            ],
        }

        result = await self.collection.insert_one(chat_data)
        return await self.collection.find_one({"_id": result.inserted_id})

    async def delete_chat(self, chat_id, user_email):
        return await self.collection.delete_one(
            {"_id": ObjectId(chat_id), "user_email": user_email}
        )

    async def update_chat(self, chat_id, data):
        return await self.collection.update_one(
            {"_id": ObjectId(chat_id)}, {"$set": data}
        )

    async def add_message(self, chat_id, message: schemas.MessageCreate):
        message_data = {
            "_id": ObjectId(),
            "sender": message.sender,
            "content": message.content,
            "timestamp": datetime.now(get_timezone()).isoformat(),
            "rating": None,
        }

        await self.collection.update_one(
            {"_id": ObjectId(chat_id)},
            {"$push": {"messages": message_data}},
        )

        return message_data

    async def update_chat_title(self, chat_id, title):
        return await self.collection.update_one(
            {"_id": ObjectId(chat_id)}, {"$set": {"name": title}}
        )

    async def update_message_rating(
        self, chat_id: ObjectId, message_id: ObjectId, rating: bool
    ):
        """
        Aggiorna la valutazione di un messaggio solo se questo è di un bot.
        """
        query_filter = {
            "_id": chat_id,
            "messages": {"$elemMatch": {"_id": message_id, "sender": "bot"}},
        }
        update_operation = {"$set": {"messages.$.rating": rating}}

        return await self.collection.update_one(query_filter, update_operation)

def get_chat_repository(db=Depends(get_db)):
    return ChatRepository(db)
