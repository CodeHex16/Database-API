from unittest.mock import MagicMock
import pytest

from app.routes.document import (
  upload_document,
  get_documents,
  delete_document,
)
from app.schemas import Document, DocumentDelete, UserAuth
from pymongo.errors import DuplicateKeyError
from fastapi import HTTPException
from bson import ObjectId
from pymongo.results import DeleteResult  

@pytest.fixture
def fake_document_repo():
    class FakeRepository:
        async def insert_document(self, owner_email, document):
            if document.title == "duplicate":
                raise DuplicateKeyError("Duplicate document")
            if document.title == "error":
                raise Exception("Some error")
            return {
                "_id": "document123",
                "title": document.title,
                "file_path": document.file_path,
                "owner_email": owner_email,
            }
        async def get_documents(self):
            return "documents"
       
        async def delete_document(self, file_id):
            MockDeleteResult = MagicMock()

            if str(file_id) == "614c1b2f8e4b0c6a1d2d5d2f":
                MockDeleteResult.deleted_count = 1
                return MockDeleteResult
            if str(file_id) == "614c1b2f8e4b0c6a1d2d5d25":
                MockDeleteResult.deleted_count = 0
                return MockDeleteResult
            if str(file_id) == "614c1b2f8e4b0c6a1d2d5d26":
                raise Exception("Some error")
    return FakeRepository()


current_user = {"sub":"hi@hi.com"}

@pytest.mark.asyncio
async def test__unit_test__upload_document(fake_document_repo):
    document = Document(title="Test Document", file_path="/path/to/document.txt")
    result = await upload_document(document,current_user, fake_document_repo)

@pytest.mark.asyncio
async def test__unit_test__upload_document_duplicate(fake_document_repo):
    document = Document(title="duplicate", file_path="/path/to/document.txt")
    with pytest.raises(HTTPException) as excinfo:
         await upload_document(document,current_user, fake_document_repo)
    assert excinfo.value.status_code == 400

@pytest.mark.asyncio
async def test__unit_test__upload_document_exception(fake_document_repo):
    document = Document(title="error", file_path="/path/to/document.txt")
    with pytest.raises(HTTPException) as excinfo:
         await upload_document(document,current_user, fake_document_repo)
    assert excinfo.value.status_code == 500


@pytest.mark.asyncio
async def test__unit_test__get_documents(fake_document_repo):
    result = await get_documents(current_user, fake_document_repo)
    assert result == "documents"

@pytest.mark.asyncio
async def test__unit_test__get_documents_erro(fake_document_repo, monkeypatch):
    async def mock_get_documents():
        return None
    monkeypatch.setattr(fake_document_repo, "get_documents", mock_get_documents)
    with pytest.raises(HTTPException) as excinfo:
        await get_documents(current_user, fake_document_repo)
    assert excinfo.value.status_code == 404

class User:
    def __init__(self):
      self._id = current_user["sub"]
    def get(self,_):
      return self._id
        
@pytest.mark.asyncio
async def test__unit_test__delete_document(fake_document_repo, monkeypatch):
    file = DocumentDelete(id="614c1b2f8e4b0c6a1d2d5d2f")
    admin = UserAuth(current_password="admin_password")

    async def mock_authenticate_user(email, password, repo):
        if email == current_user["sub"]:
            return User()
    monkeypatch.setattr("app.routes.document.authenticate_user", mock_authenticate_user)
    result = await delete_document(file, admin,current_user, fake_document_repo,None)

@pytest.mark.asyncio
async def test__unit_test__delete_document_no_valide_user(fake_document_repo, monkeypatch):
    file = DocumentDelete(id="614c1b2f8e4b0c6a1d2d5d2f")
    admin = UserAuth(current_password="admin_password")

    async def mock_authenticate_user(email, password, repo):
        return None
    monkeypatch.setattr("app.routes.document.authenticate_user", mock_authenticate_user)
    with pytest.raises(HTTPException) as excinfo:
        await delete_document(file, admin,current_user, fake_document_repo,None)
    assert excinfo.value.status_code == 401

@pytest.mark.asyncio
async def test__unit_test__delete_document_error_user(fake_document_repo, monkeypatch):
    file = DocumentDelete(id="614c1b2f8e4b0c6a1d2d5d2f")
    admin = UserAuth(current_password="admin_password")
    current_user = {"sub":"hi2@hi.com"}
    async def mock_authenticate_user(email, password, repo):
        if email == current_user["sub"]:
            return User()
    monkeypatch.setattr("app.routes.document.authenticate_user", mock_authenticate_user)
    with pytest.raises(HTTPException) as excinfo:
        await delete_document(file, admin,current_user, fake_document_repo,None)
    assert excinfo.value.status_code == 403

@pytest.mark.asyncio
async def test__unit_test__delete_document_delete_count_error(fake_document_repo, monkeypatch):
    file = DocumentDelete(id="614c1b2f8e4b0c6a1d2d5d25")
    admin = UserAuth(current_password="admin_password")
    async def mock_authenticate_user(email, password, repo):
        if email == current_user["sub"]:
            return User()
    monkeypatch.setattr("app.routes.document.authenticate_user", mock_authenticate_user)
    with pytest.raises(HTTPException) as excinfo:
        await delete_document(file, admin,current_user, fake_document_repo,None)
    assert excinfo.value.status_code == 500

@pytest.mark.asyncio
async def test__unit_test__delete_document_delete_count_exception(fake_document_repo, monkeypatch):
    file = DocumentDelete(id="614c1b2f8e4b0c6a1d2d5d26")
    admin = UserAuth(current_password="admin_password")
    async def mock_authenticate_user(email, password, repo):
        if email == current_user["sub"]:
            return User()
    monkeypatch.setattr("app.routes.document.authenticate_user", mock_authenticate_user)
    with pytest.raises(HTTPException) as excinfo:
        await delete_document(file, admin,current_user, fake_document_repo,None)
    assert excinfo.value.status_code == 500
    





    

