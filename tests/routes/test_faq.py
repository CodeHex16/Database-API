import pytest

from unittest.mock import MagicMock, AsyncMock

from app.schemas import FAQ, FAQUpdate, UserAuth
from app.routes.faq import create_faq, get_faqs, update_faq, delete_faq
from pymongo.errors import DuplicateKeyError
from fastapi import HTTPException
from bson import ObjectId

@pytest.fixture
def fake_faq_repo():
    class FakeRepository:
      async def insert_faq(self, faq: FAQ, author_email: str):
          if faq.title == "duplicate":
              raise DuplicateKeyError("Duplicate FAQ")
          if faq.title == "error":
              raise Exception("Some error")
          return {
              "_id": "faq123",
              "title": faq.title,
              "question": faq.question,
              "answer": faq.answer,
              "created_by": author_email,
          }
      async def get_faqs(self):
          return "faqs"
      async def update_faq(self, faq_id: ObjectId, faq_data: FAQUpdate, author_email: str):
          if str(faq_id) == "614c1b2f8e4b0c6a1d2d5d2f":
              return {
                  "_id": faq_id,
                  "title": faq_data.title,
                  "question": faq_data.question,
                  "answer": faq_data.answer,
                  "updated_by": author_email,
              }
          if str(faq_id) == "614c1b2f8e4b0c6a1d2d5d25":
              raise Exception("Some error")
      async def delete_faq(self, faq_id: ObjectId):
          if str(faq_id) == "614c1b2f8e4b0c6a1d2d5d2f":
              return True
          if str(faq_id) == "614c1b2f8e4b0c6a1d2d5d25":
              raise Exception("Some error")
    return FakeRepository()

current_user = {"sub":"hi@hi.com"}

@pytest.mark.asyncio
async def test__unit_test__create_faq(fake_faq_repo):
    faq = FAQ(
        title="Test FAQ",
        question="What is the purpose of this API?",
        answer="This API provides a way to interact with our service.",
    )
    result = await create_faq(faq, current_user, fake_faq_repo)
    assert result["status"] == 201

@pytest.mark.asyncio
async def test__unit_test__create_faq_duplicate(fake_faq_repo):
    faq = FAQ(
        title="duplicate",
        question="What is the purpose of this API?",
        answer="This API provides a way to interact with our service.",
    )
    with pytest.raises(HTTPException) as excinfo:
        await create_faq(faq, current_user, fake_faq_repo)
    assert excinfo.value.status_code == 400

@pytest.mark.asyncio
async def test__unit_test__create_faq_error(fake_faq_repo):
    faq = FAQ(
        title="error",
        question="What is the purpose of this API?",
        answer="This API provides a way to interact with our service.",
    )
    with pytest.raises(HTTPException) as excinfo:
        await create_faq(faq, current_user, fake_faq_repo)
    assert excinfo.value.status_code == 500

@pytest.mark.asyncio
async def test__unit_test__get_faqs(fake_faq_repo):
    result = await get_faqs(current_user, fake_faq_repo)
    assert result == "faqs"

@pytest.mark.asyncio
async def test__unit_test__get_faqs_not_found(fake_faq_repo, monkeypatch):
    monkeypatch.setattr(fake_faq_repo, "get_faqs", AsyncMock(return_value=None))
    with pytest.raises(HTTPException) as excinfo:
        await get_faqs(current_user, fake_faq_repo)
    assert excinfo.value.status_code == 404

@pytest.mark.asyncio
async def test__unit_test__update_faq(fake_faq_repo):
    faq_id = "614c1b2f8e4b0c6a1d2d5d2f"
    faq = FAQUpdate(
        title="Updated FAQ",
        question="What is the purpose of this API?",
        answer="This API provides a way to interact with our service.",
    )
    result = await update_faq(faq_id, faq, current_user, fake_faq_repo)

@pytest.mark.asyncio
async def test__unit_test__update_faq_exception(fake_faq_repo):
    faq_id = "614c1b2f8e4b0c6a1d2d5d25"
    faq = FAQUpdate(
        title="Updated FAQ",
        question="What is the purpose of this API?",
        answer="This API provides a way to interact with our service.",
    )
    with pytest.raises(HTTPException) as excinfo:
        await update_faq(faq_id, faq, current_user, fake_faq_repo)
    assert excinfo.value.status_code == 500


class User:
    def __init__(self):
      self._id = current_user["sub"]
    def get(self,_):
      return self._id
        

@pytest.mark.asyncio
async def test__unit_test__delete_faq(fake_faq_repo, monkeypatch):
    faq_id = "614c1b2f8e4b0c6a1d2d5d2f"
    admin = UserAuth(current_password="admin_password")
    async def mock_authenticate_user(email, password, repo):
        if email == current_user["sub"]:
            return User()
        
    monkeypatch.setattr("app.routes.faq.authenticate_user", mock_authenticate_user)
    result = await delete_faq(faq_id, admin, current_user, fake_faq_repo, None)

@pytest.mark.asyncio
async def test__unit_test__delete_faq_no_valid_user(fake_faq_repo, monkeypatch):
    faq_id = "614c1b2f8e4b0c6a1d2d5d2f"
    admin = UserAuth(current_password="admin_password")
    async def mock_authenticate_user(email, password, repo):
        if email == current_user["sub"]:
            return None
        
    monkeypatch.setattr("app.routes.faq.authenticate_user", mock_authenticate_user)
    with pytest.raises(HTTPException) as ex:
        await delete_faq(faq_id, admin, current_user, fake_faq_repo, None)
    assert ex.value.status_code == 401

@pytest.mark.asyncio
async def test__unit_test__delete_faq_user_error(fake_faq_repo, monkeypatch):
    faq_id = "614c1b2f8e4b0c6a1d2d5d2f"
    current_user = {"sub":"hi2@hi.com"}
    admin = UserAuth(current_password="admin_password")
    async def mock_authenticate_user(email, password, repo):
        if email == current_user["sub"]:
            return User()
        
    monkeypatch.setattr("app.routes.faq.authenticate_user", mock_authenticate_user)
    with pytest.raises(HTTPException) as ex:
        await delete_faq(faq_id, admin, current_user, fake_faq_repo, None)
    assert ex.value.status_code == 403

@pytest.mark.asyncio
async def test__unit_test__delete_faq_exception(fake_faq_repo, monkeypatch):
    faq_id = "614c1b2f8e4b0c6a1d2d5d25"
    admin = UserAuth(current_password="admin_password")
    async def mock_authenticate_user(email, password, repo):
        if email == current_user["sub"]:
            return User()
        
    monkeypatch.setattr("app.routes.faq.authenticate_user", mock_authenticate_user)
    with pytest.raises(HTTPException) as ex:
        await delete_faq(faq_id, admin, current_user, fake_faq_repo, None)
    assert ex.value.status_code == 500