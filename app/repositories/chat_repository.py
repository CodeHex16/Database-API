from bson import ObjectId
from datetime import datetime, time
from typing import Optional

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

    async def get_chat_by_id(self, chat_id, user_email, limit: int = 0):
        result = await self.collection.find_one(
            {"_id": ObjectId(chat_id), "user_email": user_email}
        )

        if limit:
            result["messages"] = result["messages"][-limit:]

        return result

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
        """
        Aggiunge un messaggio alla chat.
        """
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
        """
        Aggiorna il titolo della chat.
        """
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


    async def get_chat_stats(self, start_date: Optional[str] = None, end_date: Optional[str] = None):
        query = {}

        if start_date or end_date:
            query["created_at"] = {}

            if start_date:
                dt_start = datetime.strptime(start_date, "%Y-%m-%d")
                dt_start_str = dt_start.replace(hour=0, minute=0, second=0).isoformat() + "+02:00"
                query["created_at"]["$gte"] = dt_start_str

            if end_date:
                dt_end = datetime.strptime(end_date, "%Y-%m-%d")
                dt_end_str = dt_end.replace(hour=23, minute=59, second=59, microsecond=999999).isoformat() + "+02:00"
                query["created_at"]["$lte"] = dt_end_str

        print("Query finale:", query)

        chats = await self.collection.find(query).to_list(length=10000)

        total_chats = len(chats)
        total_messages = 0
        total_chatbot_messages = 0
        total_user_messages = 0
        user_message_counts = {}

        rated_messages_count = 0
        rated_messages_positive = 0

        for chat in chats:
            user_email = chat.get("user_email")
            messages = chat.get("messages", [])

            total_messages += len(messages)

            if user_email:
                user_message_counts[user_email] = user_message_counts.get(user_email, 0) + len(messages)

            for msg in messages:
                rating = msg.get("rating")
                if rating is not None:
                    rated_messages_count += 1
                    if rating is True:
                        rated_messages_positive += 1
                sender = msg.get("sender")
                if sender == "bot":
                    total_chatbot_messages += 1
                elif sender == "user":
                    total_user_messages += 1

        average_messages_per_user = (
            sum(user_message_counts.values()) / len(user_message_counts)
            if user_message_counts else 0
        )

        average_messages_per_chat = (
            total_messages / total_chats if total_chats > 0 else 0
        )

        rating_positive_percentage = (
            (rated_messages_positive / rated_messages_count) * 100
            if rated_messages_count > 0 else 0
        )

        return {
            "total_chats": total_chats,
            "total_messages": total_messages,
            "total_chatbot_messages": total_chatbot_messages,
            "total_rated_messages": rated_messages_count,
            "total_user_messages": total_user_messages,
            "average_messages_per_user": round(average_messages_per_user, 2),
            "average_messages_per_chat": round(average_messages_per_chat, 2),
            "positive_rating_percentage": round(rating_positive_percentage, 2),
            "active_users": len(user_message_counts),
        }

def get_chat_repository(db=Depends(get_db)):
    return ChatRepository(db)