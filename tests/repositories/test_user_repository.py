import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi import HTTPException
from app.repositories.user_repository import UserRepository, get_user_repository
from app.utils import get_password_hash
from app.schemas import User, UserUpdate


@pytest.fixture
def mock_database():
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_collection.find_one = AsyncMock()
    mock_collection.find = MagicMock()
    mock_collection.find().to_list = AsyncMock()
    mock_collection.insert_one = AsyncMock()
    mock_collection.update_one = AsyncMock()
    mock_collection.delete_one = AsyncMock()
    mock_db.get_collection.return_value = mock_collection
    return mock_db


@pytest.fixture
def user_repository(mock_database):
    return UserRepository(mock_database)


@pytest.mark.asyncio
async def test__unit_test__get_users(user_repository, mock_database):
    mock_collection = mock_database.get_collection.return_value
    mock_collection.find().to_list.return_value = [{"_id": "user@test.com"}]

    users = await user_repository.get_users()

    assert users == [{"_id": "user@test.com"}]
    mock_collection.find().to_list.assert_awaited_once()


@pytest.mark.asyncio
async def test__unit_test__get_by_email(user_repository, mock_database):
    mock_collection = mock_database.get_collection.return_value
    mock_collection.find_one.return_value = {"_id": "user@test.com"}

    user = await user_repository.get_by_email("user@test.com")

    assert user["_id"] == "user@test.com"


@pytest.mark.asyncio
async def test__unit_test__create_user(user_repository, mock_database):
    mock_collection = mock_database.get_collection.return_value
    mock_collection.insert_one.return_value = MagicMock(inserted_id="user@test.com")

    user = User(
        _id="user@test.com",
        name="Test",
        hashed_password="hash",
        is_initialized=False,
        remember_me=False,
        scopes=["user"]
    )

    result = await user_repository.create_user(user)

    mock_collection.insert_one.assert_awaited_once_with(user)
    assert result.inserted_id == "user@test.com"


@pytest.mark.asyncio
async def test__unit_test__add_test_user(user_repository, mock_database):
    mock_collection = mock_database.get_collection.return_value
    mock_collection.insert_one.return_value = MagicMock(inserted_id="test@test.it")

    result = await user_repository.add_test_user()

    mock_collection.insert_one.assert_awaited()
    assert result.inserted_id == "test@test.it"

@pytest.mark.asyncio
async def test__unit_test__add_test_user_error(user_repository, mock_database):
    mock_collection = mock_database.get_collection.return_value
    mock_collection.insert_one.side_effect = Exception("DB error")

    
    result = await user_repository.add_test_user()
    assert result is None


@pytest.mark.asyncio
async def test__unit_test__add_test_admin(user_repository, mock_database):
    mock_collection = mock_database.get_collection.return_value
    mock_collection.insert_one.return_value = MagicMock(inserted_id="admin@test.it")

    result = await user_repository.add_test_admin()

    mock_collection.insert_one.assert_awaited()
    assert result.inserted_id == "admin@test.it"

@pytest.mark.asyncio
async def test__unit_test__add_test_admin_error(user_repository, mock_database):
    mock_collection = mock_database.get_collection.return_value
    mock_collection.insert_one.side_effect = Exception("DB error")

    
    result = await user_repository.add_test_admin()

    assert result is None

@pytest.mark.asyncio
async def test__unit_test__get_test_user(user_repository, mock_database):
    mock_collection = mock_database.get_collection.return_value
    mock_collection.find_one.return_value = {"_id": "123@234.com"}

    result = await user_repository.get_test_user()

    assert result["_id"] == "123@234.com"

@pytest.mark.asyncio
async def test__unit_test__get_test_admin(user_repository, mock_database):
    mock_collection = mock_database.get_collection.return_value
    mock_collection.find_one.return_value = {"_id": "admin@admin.com"}

    result = await user_repository.get_test_admin()

    assert result["_id"] == "admin@admin.com"

@pytest.mark.asyncio
async def test__unit_test__delete_user_success(user_repository, mock_database):
    mock_collection = mock_database.get_collection.return_value
    mock_collection.delete_one.return_value = MagicMock(deleted_count=1)

    await user_repository.delete_user("user@test.com")

    mock_collection.delete_one.assert_awaited_once_with({"_id": "user@test.com"})

@pytest.mark.asyncio
async def test__unit_test__delete_user_error(user_repository, mock_database):
    mock_collection = mock_database.get_collection.return_value
    mock_collection.delete_one.side_effect = Exception("DB error")

    with pytest.raises(Exception) as exc_info:
        await user_repository.delete_user("213@123.com")


@pytest.mark.asyncio
async def test__unit_test__delete_user_not_found(user_repository, mock_database):
    mock_collection = mock_database.get_collection.return_value
    mock_collection.delete_one.return_value = MagicMock(deleted_count=0)

    with pytest.raises(HTTPException) as exc_info:
        await user_repository.delete_user("nonexistent@test.com")

    assert exc_info.value.status_code == 404
    assert "not found" in exc_info.value.detail.lower()



@pytest.mark.asyncio
async def test__unit_test__update_user_success(user_repository, mock_database):
    mock_collection = mock_database.get_collection.return_value
    mock_collection.find_one.return_value = {
        "_id": "user@test.com",
        "password": "passsswod",
        "is_initialized": False,
        "remember_me": False,
        "scopes": ["user"]
    }
    mock_collection.update_one.return_value = MagicMock(modified_count=1)

    update_data = UserUpdate(
         _id = "user@test.com",
        name="Test",
        password="newpass",
        is_initialized=True,
        remember_me=True,
        scopes=["admin"]
    )

    result = await user_repository.update_user("user@test.com", update_data)

    assert result.modified_count == 1
    mock_collection.update_one.assert_awaited_once()

@pytest.mark.asyncio
async def test__unit_test__update_user_success_with_no_password(user_repository, mock_database):
    mock_collection = mock_database.get_collection.return_value
    mock_collection.find_one.return_value = {
        "_id": "user@test.com",
        "password": "passsswod",
        "is_initialized": False,
        "remember_me": False,
        "scopes": ["user"]
    }
    mock_collection.update_one.return_value = MagicMock(modified_count=1)

    update_data = UserUpdate(
         _id = "user@test.com",
        is_initialized=True,
        remember_me=True,
        scopes=["admin"]
    )

    result = await user_repository.update_user("user@test.com", update_data)

    assert result.modified_count == 1
    mock_collection.update_one.assert_awaited_once()


@pytest.mark.asyncio
async def test__unit_test__update_user_error(user_repository, mock_database):
    mock_collection = mock_database.get_collection.return_value
    mock_collection.find_one.return_value = {
        "_id": "user@test.com",
        "password": "passsswod",
        "is_initialized": False,
        "remember_me": False,
        "scopes": ["user"]
    }
    mock_collection.update_one.side_effect = Exception("DB error")

    update_data = UserUpdate(
         _id = "user@test.com",
        password="newpass",
        is_initialized=True,
        remember_me=True,
        scopes=["admin"]
    )
    with pytest.raises(HTTPException) as exc_info:
        result = await user_repository.update_user("user@test.com", update_data)
    assert exc_info.value.status_code == 500

               
@pytest.mark.asyncio
async def test__unit_test__update_user_no_changes_provide(user_repository, mock_database):
    update_data = UserUpdate(_id=None)
    with pytest.raises(HTTPException) as exc_info:
        await user_repository.update_user("user@test.com", update_data)
    assert exc_info.value.status_code == 400

@pytest.mark.asyncio
async def test__unit_test__update_user_no_modified(user_repository, mock_database):
    mock_collection = mock_database.get_collection.return_value
    mock_collection.find_one.return_value = {
        "_id": "user@test.com",
        "hashed_password": "$2b$12$zqt9Rgv1PzORjG5ghJSb6OSdYrt7f7cLc38a21DgX/DMyqt80AUCi",
        "is_initialized": False,
        "remember_me": False,
        "scopes": ["admin"]
    }
    mock_collection.update_one.return_value = MagicMock(modified_count=1)

    update_data = UserUpdate(
        _id = "user@test.com",
        password="test_password",
        is_initialized=False,
        remember_me=False,
        scopes=["admin"]
    )

    with pytest.raises(HTTPException) as exc_info:
        await user_repository.update_user("ee@eeexample.com", update_data)

    assert exc_info.value.status_code == 304


@pytest.mark.asyncio
async def test__unit_test__update_user_not_found(user_repository, mock_database):
    mock_collection = mock_database.get_collection.return_value
    mock_collection.find_one.return_value = None

    update_data = UserUpdate(_id="test@test.com",password="anypass")

    with pytest.raises(HTTPException) as exc_info:
        await user_repository.update_user("missing@test.com", update_data)

    assert exc_info.value.status_code == 404

@pytest.mark.asyncio
async def test__unit_test__get_user_repository_returns_instance(mock_database):
    test_db = mock_database["test_database"]
    repo = get_user_repository(test_db)
    assert isinstance(repo, UserRepository)