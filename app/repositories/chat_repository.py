from bson import ObjectId
from datetime import datetime
import uuid


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
            "created_at": datetime.now(),
            "messages": [
                {
                    "sender": "bot",
                    "content": "Ciao, sono SupplAI, il tuo assistente per gli acquisti personale! Come posso aiutarti?",
                    "timestamp": datetime.now(),
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

    async def add_message(self, chat_id, message):
        message_data = {
            "sender": message["sender"],
            "content": message["content"],
            "timestamp": datetime.now(),
        }

        return await self.collection.update_one(
            {"_id": ObjectId(chat_id)},
            {"$push": {"messages": message_data}},
        )

    async def update_chat_title(self, chat_id, title):
        return await self.collection.update_one(
            {"_id": ObjectId(chat_id)}, {"$set": {"name": title}}
        )