import pytest
from unittest.mock import MagicMock, AsyncMock, ANY
from datetime import datetime
from bson import ObjectId
from app.repositories.chat_repository import ChatRepository
from app.schemas import MessageCreate

@pytest.fixture
def mock_database():
    # Create a mock database object with AsyncMock for async methods
    mock_db = MagicMock()
    mock_collection = MagicMock()
    
    # Use AsyncMock for async methods like find, insert_one, update_one, etc.
    mock_collection.find.return_value.to_list = AsyncMock(return_value=[])
    mock_collection.insert_one = AsyncMock()
    mock_collection.delete_one = AsyncMock()
    mock_collection.update_one = AsyncMock()
    mock_db.get_collection.return_value = mock_collection
    return mock_db


@pytest.fixture
def chat_repository(mock_database):
    # Create an instance of ChatRepository with the mock database
    return ChatRepository(mock_database)


@pytest.mark.asyncio
async def test__unit_test__get_chat_by_user_email(chat_repository, mock_database):
    # Define test data
    test_email = "testuser@example.com"
    chat_data = [{"_id": ObjectId(), "name": "Test Chat", "user_email": test_email, "messages": []}]
    
    # Mock the collection's find method
    mock_database.get_collection().find.return_value.to_list.return_value = chat_data

    # Call the method
    chats = await chat_repository.get_chat_by_user_email(test_email)

    # Assertions
    assert len(chats) == 1
    assert chats[0]["user_email"] == test_email


@pytest.mark.asyncio
async def test__unit_test__get_chat_by_id(chat_repository, mock_database):
    # Define test data
    test_chat_id = ObjectId()
    test_email = ANY
    chat_data = {
        "_id": test_chat_id,
        "name": "Test Chat",
        "user_email": test_email,
        "messages": [],
    }
    mock_database.get_collection().find_one = AsyncMock(return_value=chat_data)
    chats = await chat_repository.get_chat_by_id(str(test_chat_id), test_email)

    assert chats["_id"] == test_chat_id
    assert chats["name"] == "Test Chat"
    assert chats["user_email"] == test_email


@pytest.mark.asyncio
async def test__unit_test__initialize_chat(chat_repository, mock_database):
    # Define test data
    test_email = "testuser@example.com"
    initial_message = {
        "_id": ObjectId(),
        "sender": "bot",
        "content": "Ciao, sono SupplAI, il tuo assistente per gli acquisti personale! Come posso aiutarti?",
        "timestamp": datetime.now().isoformat(),
        "rating": None,
    }

    # Mock the insert_one method to return an object with inserted_id
    mock_insert_result = MagicMock()
    mock_insert_result.inserted_id = ObjectId()
    mock_database.get_collection().insert_one = AsyncMock(return_value=mock_insert_result)

    # Mock the find_one method to return a sample chat document
    mock_database.get_collection().find_one = AsyncMock(return_value={
        "_id": mock_insert_result.inserted_id,
        "name": "Chat senza nome",
        "user_email": test_email,
        "created_at": datetime.now().isoformat(),
        "messages": [initial_message],
    })

    # Call the method
    chat = await chat_repository.initialize_chat(test_email)

    # Assertions
    assert chat["user_email"] == test_email
    assert len(chat["messages"]) == 1
    assert chat["messages"][0]["content"] == initial_message["content"]

@pytest.mark.asyncio
async def test__unit_test__delete_chat(chat_repository, mock_database):
    # Define test data
    test_chat_id = ObjectId()
    test_email = "testuser@example.com"
    
    # Mock the delete_one method
    mock_database.get_collection().delete_one.return_value.deleted_count = 1

    # Call the method
    result = await chat_repository.delete_chat(str(test_chat_id), test_email)

    # Assertions
    mock_database.get_collection().delete_one.assert_called_once_with({"_id": test_chat_id, "user_email": test_email})
    assert result.deleted_count == 1

@pytest.mark.asyncio
async def test__unit_test__update_chat(chat_repository, mock_database):
    # Define test data
    test_chat_id = ObjectId()
    update_data = {"name": "Updated Chat Name"}

    # Mock the update_one method
    mock_database.get_collection().update_one.return_value.modified_count = 1

    # Call the method
    result = await chat_repository.update_chat(str(test_chat_id), update_data)

    # Assertions
    mock_database.get_collection().update_one.assert_called_once_with(
        {"_id": test_chat_id},
        {"$set": update_data},
    )
    assert result.modified_count == 1


@pytest.mark.asyncio
async def test__unit_test__add_message(chat_repository, mock_database, monkeypatch):
    # Define test data
    test_chat_id = ObjectId()
    test_message = MessageCreate(content="Hello!", sender="user")
    message_data = {
        "_id": ANY,
        "sender": test_message.sender,
        "content": test_message.content,
        "timestamp": ANY,
        "rating": None,
    }

    # Mock the update_one method
    mock_database.get_collection().update_one = AsyncMock(return_value=AsyncMock(modified_count=1))

    added_message = await chat_repository.add_message(str(test_chat_id), test_message)

    # Assertions
    assert added_message["content"] == message_data["content"]
    assert added_message["sender"] == message_data["sender"]

    # Assert the update_one method was called with the expected arguments
    mock_database.get_collection().update_one.assert_called_once_with(
        {"_id": test_chat_id},
        {"$push": {"messages": message_data}},
    )

@pytest.mark.asyncio
async def test__unit_test__update_chat_title(chat_repository, mock_database):
    # Define test data
    test_chat_id = ObjectId()
    new_title = "Updated Chat Name"

    # Mock the update_one method
    mock_database.get_collection().update_one.return_value.modified_count = 1

    # Call the method
    result = await chat_repository.update_chat_title(str(test_chat_id), new_title)

    # Assertions
    mock_database.get_collection().update_one.assert_called_once_with(
        {"_id": test_chat_id},
        {"$set": {"name": new_title}},
    )
    assert result.modified_count == 1

@pytest.mark.asyncio
async def test__unit_test__update_message_rating(chat_repository, mock_database):
    # Define test data
    test_chat_id = ObjectId()
    test_message_id = ObjectId()
    rating_data = {"rating": True}

    # Mock the update_one method
    mock_database.get_collection().update_one.return_value.modified_count = 1


    # Call the method
    result = await chat_repository.update_message_rating(str(test_chat_id), str(test_message_id), rating_data)

    # Assertions
    mock_database.get_collection().update_one.assert_called_once_with(
      ANY,  # ignore exact filter, or partially match it yourself
      ANY   # ignore exact update expression
    )
    assert result.modified_count == 1