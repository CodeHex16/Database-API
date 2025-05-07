import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime
from bson import ObjectId
from pymongo.errors import DuplicateKeyError

from app.repositories.document_repository import DocumentRepository
from app.schemas import Document


@pytest.fixture
def mock_database():
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_collection.find.return_value.to_list = AsyncMock(return_value=[])
    mock_collection.insert_one = AsyncMock()
    mock_collection.delete_one = AsyncMock()
    mock_db.get_collection.return_value = mock_collection
    return mock_db


@pytest.fixture
def document_repository(mock_database):
    return DocumentRepository(mock_database)


@pytest.mark.asyncio
async def test__unit_test__get_documents(document_repository, mock_database):
    expected_documents = [{"_id": ObjectId(), "title": "Doc 1", "file_path": "/tmp/a.txt"}]
    mock_database.get_collection().find.return_value.to_list.return_value = expected_documents
    result = await document_repository.get_documents()
    assert result == expected_documents


@pytest.mark.asyncio
async def test__unit_test__insert_document_success(document_repository, mock_database, monkeypatch):
    email = "test@example.com"
    doc = Document(title="Test", file_path="/test/path.txt")

    mock_result = MagicMock()
    mock_database.get_collection().insert_one = AsyncMock(return_value=mock_result)

    mock_object_id = ObjectId()
    monkeypatch.setattr("app.repositories.document_repository.get_object_id", lambda path: mock_object_id)
    monkeypatch.setattr("app.repositories.document_repository.get_timezone", lambda: datetime.now().astimezone().tzinfo)

    result = await document_repository.insert_document(email, doc)
    assert result == mock_result
    mock_database.get_collection().insert_one.assert_called_once()
    args, _ = mock_database.get_collection().insert_one.call_args
    inserted_doc = args[0]
    assert inserted_doc["_id"] == mock_object_id
    assert inserted_doc["title"] == doc.title
    assert inserted_doc["file_path"] == doc.file_path
    assert inserted_doc["owner_email"] == email

@pytest.mark.asyncio
async def test__unit_test__insert_document_error(document_repository, mock_database, monkeypatch):
    email = "test@example.com"
    doc = Document(title="Test", file_path="/test/path.txt")

    mock_database.get_collection().insert_one = AsyncMock(side_effect=Exception("Database error"))

    monkeypatch.setattr("app.repositories.document_repository.get_object_id", lambda path: ObjectId())
    monkeypatch.setattr("app.repositories.document_repository.get_timezone", lambda: datetime.now().astimezone().tzinfo)


    with pytest.raises(Exception):
        await document_repository.insert_document(email, doc)


@pytest.mark.asyncio
async def test__unit_test__insert_document_duplicate_key(document_repository, mock_database, monkeypatch):
    email = "test@example.com"
    doc = Document(title="Test", file_path="/test/path.txt")

    monkeypatch.setattr("app.repositories.document_repository.get_object_id", lambda path: ObjectId())
    monkeypatch.setattr("app.repositories.document_repository.get_timezone", lambda: datetime.now().astimezone().tzinfo)

    mock_database.get_collection().insert_one = AsyncMock(side_effect=DuplicateKeyError("duplicate key error"))

    with pytest.raises(DuplicateKeyError):
        await document_repository.insert_document(email, doc)


@pytest.mark.asyncio
async def test__unit_test__delete_document(document_repository, mock_database):
    file_id = ObjectId()
    mock_result = MagicMock(deleted_count=1)
    mock_database.get_collection().delete_one = AsyncMock(return_value=mock_result)

    result = await document_repository.delete_document(file_id)
    assert result.deleted_count == 1
    mock_database.get_collection().delete_one.assert_called_once_with({"_id": file_id})

@pytest.mark.asyncio
async def test__unit_test__delete_document_error(document_repository, mock_database):
    file_id = ObjectId()
    mock_database.get_collection().delete_one = AsyncMock(side_effect=Exception("Database error"))

    with pytest.raises(Exception):
        await document_repository.delete_document(file_id)