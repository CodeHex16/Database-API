import pytest
from unittest.mock import AsyncMock, MagicMock
from bson import ObjectId
from datetime import datetime
from pymongo.errors import DuplicateKeyError
from fastapi import HTTPException

from app.repositories.faq_repository import FaqRepository, get_faq_repository
from app.schemas import FAQ, FAQUpdate


@pytest.fixture
def mock_database():
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_collection.find.return_value.to_list = AsyncMock(return_value=[])
    mock_collection.find_one = AsyncMock()
    mock_collection.insert_one = AsyncMock()
    mock_collection.update_one = AsyncMock()
    mock_collection.delete_one = AsyncMock()
    mock_db.get_collection.return_value = mock_collection
    return mock_db


@pytest.fixture
def faq_repository(mock_database):
    return FaqRepository(mock_database)


@pytest.mark.asyncio
async def test_get_faqs(faq_repository, mock_database):
    expected_faqs = [{"_id": ObjectId(), "title": "Q1", "question": "?", "answer": "A"}]
    mock_database.get_collection().find.return_value.to_list.return_value = expected_faqs
    result = await faq_repository.get_faqs()
    assert result == expected_faqs


@pytest.mark.asyncio
async def test_get_faq_by_id_success(faq_repository, mock_database):
    faq_id = ObjectId()
    expected_faq = {"_id": faq_id, "title": "Q1", "question": "?", "answer": "A"}
    mock_database.get_collection().find_one.return_value = expected_faq
    result = await faq_repository.get_faq_by_id(faq_id)
    assert result == expected_faq


@pytest.mark.asyncio
async def test_get_faq_by_id_error(faq_repository, mock_database):
    faq_id = ObjectId()
    mock_database.get_collection().find_one = AsyncMock(side_effect=Exception("DB error"))
    with pytest.raises(Exception, match="Error retrieving FAQ"):
        await faq_repository.get_faq_by_id(faq_id)


@pytest.mark.asyncio
async def test_insert_faq_success(faq_repository, mock_database, monkeypatch):
    faq = FAQ(title="T", question="Q", answer="A")
    mock_result = MagicMock(inserted_id="abc")
    mock_database.get_collection().insert_one = AsyncMock(return_value=mock_result)
    monkeypatch.setattr("app.repositories.faq_repository.get_timezone", lambda: datetime.now().astimezone().tzinfo)

    result = await faq_repository.insert_faq(faq, "user@example.com")
    assert result == "abc"
    mock_database.get_collection().insert_one.assert_called_once()


@pytest.mark.asyncio
async def test_insert_faq_duplicate_key(faq_repository, mock_database, monkeypatch):
    faq = FAQ(title="T", question="Q", answer="A")
    monkeypatch.setattr("app.repositories.faq_repository.get_timezone", lambda: datetime.now().astimezone().tzinfo)
    mock_database.get_collection().insert_one = AsyncMock(side_effect=DuplicateKeyError("dup"))

    with pytest.raises(DuplicateKeyError):
        await faq_repository.insert_faq(faq, "user@example.com")


@pytest.mark.asyncio
async def test_insert_faq_general_error(faq_repository, mock_database, monkeypatch):
    faq = FAQ(title="T", question="Q", answer="A")
    monkeypatch.setattr("app.repositories.faq_repository.get_timezone", lambda: datetime.now().astimezone().tzinfo)
    mock_database.get_collection().insert_one = AsyncMock(side_effect=Exception("error"))

    with pytest.raises(Exception, match="Error inserting FAQ"):
        await faq_repository.insert_faq(faq, "user@example.com")


@pytest.mark.asyncio
async def test_update_faq_success(faq_repository, mock_database, monkeypatch):
    faq_id = ObjectId()
    faq_data = FAQUpdate(title="New", question="NewQ", answer="NewA")
    current_data = {"_id": faq_id, "title": "Old", "question": "OldQ", "answer": "OldA"}

    monkeypatch.setattr("app.repositories.faq_repository.get_timezone", lambda: datetime.now().astimezone().tzinfo)
    mock_database.get_collection().find_one.return_value = current_data
    mock_result = MagicMock(matched_count=1)
    mock_database.get_collection().update_one = AsyncMock(return_value=mock_result)

    await faq_repository.update_faq(faq_id, faq_data, "user@example.com")
    mock_database.get_collection().update_one.assert_called_once()

@pytest.mark.asyncio
async def test_update_faq_not_updated(faq_repository, mock_database, monkeypatch):
    # Test data setup
    faq_id = ObjectId()
    faq_data = FAQUpdate(title="Nop", question="Same", answer="Same")
    current_data = {"_id": faq_id, "title": "Same", "question": "Same", "answer": "Same"}

    # Mocking the `get_timezone` function
    monkeypatch.setattr("app.repositories.faq_repository.get_timezone", lambda: datetime.now().astimezone().tzinfo)

    # Mocking the database operations
    mock_database.get_collection().find_one.return_value = current_data
    mock_result = MagicMock()
    mock_result.matched_count = 0  # Simulate no document being updated
    mock_database.get_collection().update_one = AsyncMock(return_value=mock_result)

    # Create an instance of the FaqRepository
    faq_repository = FaqRepository(mock_database)

    # Ensure that the exception is raised due to `matched_count == 0`
    with pytest.raises(Exception) as exc_info:
        await faq_repository.update_faq(faq_id, faq_data, "user@example.com")
    
@pytest.mark.asyncio
async def test_update_faq_not_found(faq_repository, mock_database):
    faq_id = ObjectId()
    faq_data = FAQUpdate(title="X", question="Y", answer="Z")
    mock_database.get_collection().find_one.return_value = None

    with pytest.raises(Exception) as e:
        await faq_repository.update_faq(faq_id, faq_data, "email")


@pytest.mark.asyncio
async def test_update_faq_not_modified(faq_repository, mock_database):
    faq_id = ObjectId()
    faq_data = FAQUpdate(title="Same", question="Same", answer="Same")
    mock_database.get_collection().find_one.return_value = {
        "title": "Same", "question": "Same", "answer": "Same"
    }

    with pytest.raises(Exception) as e:
        await faq_repository.update_faq(faq_id, faq_data, "email")


@pytest.mark.asyncio
async def test_update_faq_error(faq_repository, mock_database, monkeypatch):
    faq_id = ObjectId()
    faq_data = FAQUpdate(title="A", question="B", answer="C")
    mock_database.get_collection().find_one.return_value = {
        "title": "Old", "question": "Old", "answer": "Old"
    }

    monkeypatch.setattr("app.repositories.faq_repository.get_timezone", lambda: datetime.now().astimezone().tzinfo)
    mock_database.get_collection().update_one = AsyncMock(side_effect=Exception("error"))

    with pytest.raises(Exception, match="Error updating FAQ"):
        await faq_repository.update_faq(faq_id, faq_data, "email")


@pytest.mark.asyncio
async def test_delete_faq_success(faq_repository, mock_database):
    faq_id = ObjectId()
    mock_result = MagicMock(deleted_count=1)
    mock_database.get_collection().delete_one = AsyncMock(return_value=mock_result)

    result = await faq_repository.delete_faq(faq_id)
    assert result.deleted_count == 1
    mock_database.get_collection().delete_one.assert_called_once_with({"_id": faq_id})


@pytest.mark.asyncio
async def test_delete_faq_error(faq_repository, mock_database):
    faq_id = ObjectId()
    mock_database.get_collection().delete_one = AsyncMock(side_effect=Exception("error"))

    with pytest.raises(Exception, match="Error deleting FAQ"):
        await faq_repository.delete_faq(faq_id)

@pytest.mark.asyncio
async def test_get_faq_repository_returns_instance(mock_database):
    test_db = mock_database["test_database"]
    repo = get_faq_repository(test_db)
    assert isinstance(repo, FaqRepository)