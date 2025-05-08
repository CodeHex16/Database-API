import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi import APIRouter, Depends, HTTPException, status
import app.schemas as schemas
# updateresult
from pymongo.results import UpdateResult

from app.routes.chat import (
  get_new_chat,
  get_chats,
  change_chat_name,
  delete_chat,
  add_message_to_chat,
  get_chat_messages,
  rate_message
)
from bson import ObjectId

@pytest.fixture
def fake_chat_repo():
    class FakeChatRepository:
        async def initialize_chat(self, user_email):
            return {
                "_id": "chat123",
                "name": "Test Chat",
                "user_email": user_email,
                "messages": [],
            }
        async def get_chat_by_user_email(self, user_email):
            if user_email == "hi@hi.com":
                return [
                    {"_id": "chat123", "name": "Test Chat", "user_email": user_email, "messages": []},
                    {"_id": "chat456", "name": "Test Chat 456", "user_email": user_email, "messages": []}
                    ]
        async def get_chat_by_id(self, chat_id, user_email):
            print(chat_id, user_email)
            if chat_id == "chat123" or chat_id == b'foo-bar-quux':
                return {
                    "_id": 'foo-bar-quux',
                    "name": "Test Chat",
                    "user_email": user_email,
                    "messages": [],
                }
            return None
        async def update_chat(self, chat_id, chat_data):
            return 1
        async def delete_chat(self, chat_id, user_email):
            return 1
        async def add_message(self, chat_id, message: schemas.MessageCreate):
            return {
                "_id": "message123",
                "sender": message.sender,
                "content": message.content,
                "timestamp": "2023-10-01T00:00:00Z",
                "rating": None,
            }
        async def update_message_rating(self, chat_id, message_id: ObjectId, rating_data):

            MockUpdateResult = MagicMock()
            if str(message_id) == "614c1b2f8e4b0c6a1d2d5d2f":
                MockUpdateResult.matched_count = 1
                MockUpdateResult.modified_count = 1
                return MockUpdateResult
            if str(message_id) == '614c1b2f8e4b0c6a1d2d5d21':
                MockUpdateResult.matched_count = 1
                MockUpdateResult.modified_count = 0
                return MockUpdateResult
            if str(message_id) == '614c1b2f8e4b0c6a1d2d5d29':
                MockUpdateResult.matched_count = 0
                MockUpdateResult.modified_count = 0
                return MockUpdateResult
            if str(message_id) == '614c1b2f8e4b0c6a1d2d5d25':
                raise HTTPException(status_code=500, detail="Internal Server Error")
            if str(message_id) == '614c1b2f8e4b0c6a1d2d5d26':
                raise Exception(status_code=504, detail="Internal Server Error")
    return FakeChatRepository()
        
@pytest.mark.asyncio
async def test_get_new_chat(fake_chat_repo):
    current_user = {"sub":"hi@hi.com"}
    chat = await get_new_chat(current_user, fake_chat_repo)
    assert chat["chat_id"] == "chat123"

@pytest.mark.asyncio
async def test_get_new_chat_no_email(fake_chat_repo):
    current_user = {"sub":""}
    with pytest.raises(HTTPException) as excinfo:
        await get_new_chat(current_user, fake_chat_repo)
    assert excinfo.value.status_code == 400

@pytest.mark.asyncio
async def test_get_new_chat_no_chat(fake_chat_repo):
    current_user = {"sub":"hi@hi.com"}
    chat = await get_chats(current_user, fake_chat_repo)
    assert chat[0]["id"] == "chat123"

@pytest.mark.asyncio
async def test_get_new_chat_no_chat_no_email(fake_chat_repo):
    current_user = {"sub":""}
    with pytest.raises(HTTPException) as excinfo:
        await get_chats(current_user, fake_chat_repo)
    assert excinfo.value.status_code == 400

@pytest.mark.asyncio
async def test_change_chat_name(fake_chat_repo):
    current_user = {"sub":"hi@hi.com"}
    chat_id = "chat123"
    await change_chat_name(chat_id, "New Chat Name", current_user, fake_chat_repo)
    
@pytest.mark.asyncio
async def test_change_chat_name_not_found(fake_chat_repo):
    current_user = {"sub":"hi@hi.com"}
    chat_id = "chat124"
    with pytest.raises(HTTPException) as excinfo:
        await change_chat_name(chat_id, "New Chat Name", current_user, fake_chat_repo)
    assert excinfo.value.status_code == 404
     
@pytest.mark.asyncio
async def test_delete_chat(fake_chat_repo):
    current_user = {"sub":"hi@hi.com"}
    chat_id = "chat123"
    await delete_chat(chat_id, current_user, fake_chat_repo)

@pytest.mark.asyncio
async def test_delete_chat_not_found(fake_chat_repo):
    current_user = {"sub":"hi@hi.com"}
    chat_id = "chat124"
    with pytest.raises(HTTPException) as excinfo:
        await delete_chat(chat_id, current_user, fake_chat_repo)
    assert excinfo.value.status_code == 404
                    
@pytest.mark.asyncio
async def test_add_message_to_chat(fake_chat_repo):
    current_user = {"sub":"hi@hi.com"}
    chat_id = "chat123"
    message = schemas.MessageCreate(content="Hello!", sender="user")
    result = await add_message_to_chat(chat_id, message, current_user, fake_chat_repo) 
    assert result["_id"] == "message123"

@pytest.mark.asyncio
async def test_add_message_to_chat_not_found(fake_chat_repo):
    current_user = {"sub":"hi@hi.com"}
    chat_id = "chat124"
    message = schemas.MessageCreate(content="Hello!", sender="user")
    with pytest.raises(HTTPException) as excinfo:
        await add_message_to_chat(chat_id, message, current_user, fake_chat_repo)
    assert excinfo.value.status_code == 404

@pytest.mark.asyncio
async def test_get_chat_messages(fake_chat_repo):
    current_user = {"sub":"hi@hi.com"}
    chat_id = "chat123"
    messages = await get_chat_messages(chat_id, current_user, fake_chat_repo)
    assert messages["messages"] == []

@pytest.mark.asyncio
async def test_get_chat_messages_not_found(fake_chat_repo):
    current_user = {"sub":"hi@hi.com"}
    chat_id = "chat125"
    with pytest.raises(HTTPException) as excinfo:
        await get_chat_messages(chat_id, current_user, fake_chat_repo)
    assert excinfo.value.status_code == 404

@pytest.mark.asyncio
async def test_rate_message(fake_chat_repo):
    current_user = {"sub":"hi@hi.com"}
    chat_id = b'foo-bar-quux'
    message_id = "614c1b2f8e4b0c6a1d2d5d2f"
    rating_data = schemas.MessageRatingUpdate(rating=True)

    result = await rate_message(chat_id, message_id, rating_data, current_user, fake_chat_repo)

@pytest.mark.asyncio
async def test_rate_message_no_chat(fake_chat_repo):
    current_user = {"sub":"hi@hi.com"}
    chat_id = b'foo-bar-quuu'
    message_id = "614c1b2f8e4b0c6a1d2d5d2f"
    rating_data = schemas.MessageRatingUpdate(rating=True)
    with pytest.raises(HTTPException) as excinfo:
        await rate_message(chat_id, message_id, rating_data, current_user, fake_chat_repo)
    assert excinfo.value.status_code == 404

@pytest.mark.asyncio
async def test_rate_message_no_message(fake_chat_repo):
    current_user = {"sub":"hi@hi.com"}
    chat_id = b'foo-bar-quux'
    message_id = "614c1b2f8e4b0c6a1d2d5d29"
    rating_data = schemas.MessageRatingUpdate(rating=True)
    with pytest.raises(HTTPException) as excinfo:
        await rate_message(chat_id, message_id, rating_data, current_user, fake_chat_repo)
    assert excinfo.value.status_code == 404

@pytest.mark.asyncio
async def test_rate_message_no_edit(fake_chat_repo):
    current_user = {"sub":"hi@hi.com"}
    chat_id = b'foo-bar-quux'
    message_id = "614c1b2f8e4b0c6a1d2d5d21"
    rating_data = schemas.MessageRatingUpdate(rating=True)
    with pytest.raises(HTTPException) as excinfo:
        await rate_message(chat_id, message_id, rating_data, current_user, fake_chat_repo)
    assert excinfo.value.status_code == 304

@pytest.mark.asyncio
async def test_rate_message_internal_error(fake_chat_repo):
    current_user = {"sub":"hi@hi.com"}
    chat_id = b'foo-bar-quux'
    message_id = "614c1b2f8e4b0c6a1d2d5d25"
    rating_data = schemas.MessageRatingUpdate(rating=True)
    with pytest.raises(HTTPException) as excinfo:
        await rate_message(chat_id, message_id, rating_data, current_user, fake_chat_repo)
    assert excinfo.value.status_code == 500

@pytest.mark.asyncio
async def test_rate_message_internal_error_2(fake_chat_repo):
    current_user = {"sub":"hi@hi.com"}
    chat_id = b'foo-bar-quux'
    message_id = "614c1b2f8e4b0c6a1d2d5d26"
    rating_data = schemas.MessageRatingUpdate(rating=True)
    with pytest.raises(HTTPException) as excinfo:
        await rate_message(chat_id, message_id, rating_data, current_user, fake_chat_repo)
    assert excinfo.value.status_code == 500

                    