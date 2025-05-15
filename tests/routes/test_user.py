import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi import HTTPException
from app.schemas import (
    UserCreate,
    UserDelete,
    UserUpdate,
    UserAuth,
    UserUpdatePassword,
    UserForgotPassword,
)
from app.auth_roles import AccessRoles
from pymongo.errors import DuplicateKeyError
from jose import jwt, JWTError
from app.routes.user import (
    register_user,
    get_users,
    get_user,
    delete_user as delete_user_fn,
    update_user,
    update_password,
    reset_password,
)


@pytest.fixture
def fake_user_repo():
    class FakeRepository:
        async def create_user(self, user_data: UserCreate):
            if user_data["name"] == "duplicate":
                raise DuplicateKeyError("duplicate error")
            if user_data["name"] == "error":
                raise Exception("error")
            return "ok"

        async def get_users(self):
            return True

        async def get_by_email(self, email: str):
            if email == "hi@hi.com":
                return {
                    "_id": "user123",
                    "name": "Bob",
                    "email": email,
                    "scopes": AccessRoles.USER,
                    "hashed_password": "$2b$12$zqt9Rgv1PzORjG5ghJSb6OSdYrt7f7cLc38a21DgX/DMyqt80AUCi",
                    "is_initialized": True,
                }
            # if email == "hi2@hi.com":
            #     return {
            #         "_id": "user123",
            #         "name": "Bob",
            #         "email": email,
            #         "scopes": AccessRoles.USER,
            #         "hashed_password": "$2b$12$zqt9Rgv1PzORjG5ghJSb6OSdYrt7f7cLc38a21DgX/DMyqt80AUCi",
            #         "is_initialized": False,
            #     }
            # if email == "hi3@hi.com":
            #     return {
            #         "_id": "user123",
            #         "name": "Bob",
            #         "email": email,
            #         "scopes": AccessRoles.USER,
            #         "hashed_password": "$2b$12$zqt9Rgv1PzORjG5ghJSb6OSdYrt7f7cLc38a21DgX/DMyqt80AUCi",
            #         "is_initialized": False,
            #     }
            if email == "hi4@hi.com":
                return {
                    "_id": "user123",
                    "name": "Bob",
                    "email": email,
                    "scopes": AccessRoles.USER,
                    "hashed_password": "$2b$12$zqt9Rgv1PzORjG5ghJSb6OSdYrt7f7cLc38a21DgX/DMyqt80AUCi",
                    "is_initialized": False,
                }

        async def update_user(self, user_id: str, user_data: UserUpdate):
            MockUpdateResult = MagicMock()
            print(user_id, user_data)
            if user_id == "hi@hi.com" or user_id == "hihi@hi.com":
                MockUpdateResult.modified_count = 1
                MockUpdateResult.matched_count = 1
                return MockUpdateResult
            if user_id == "hi3@hi.com":
                MockUpdateResult.modified_count = 0
                MockUpdateResult.matched_count = 1
                return MockUpdateResult

            if user_id == "error@error.com":
                raise Exception("error")
            MockUpdateResult.modified_count = 0
            MockUpdateResult.matched_count = 0
            return MockUpdateResult

        async def delete_user(self, user_id: str):
            if user_id == "user123@asd.com":
                return True
            if user_id == "error@asd.com":
                raise Exception("error")
            if user_id == "jwterror@asd.com":
                raise JWTError("error")

    return FakeRepository()


current_user = {"sub": "hi@hi.com"}


@pytest.mark.asyncio
async def test__unit_test__register_user(fake_user_repo, monkeypatch): 
    user_data = UserCreate(name="Bob", email="hi@hi.com", scopes=AccessRoles.USER)

    mock_email_service_instance = AsyncMock()
    mock_email_service_instance.send_email = AsyncMock(return_value=None)

    class MockEmailService:
        def __init__(self):
            pass 
        async def send_email(self, to, subject, body):
            return await mock_email_service_instance.send_email(to, subject, body)

    monkeypatch.setattr("app.routes.user.EmailService", MockEmailService)

    result = await register_user(user_data, current_user, fake_user_repo)
    assert result["message"] != None


@pytest.mark.asyncio
async def test__unit_test__register_user_duplicate(fake_user_repo):
    user_data = UserCreate(name="duplicate", email="hi@hi.com", scopes=AccessRoles.USER)
    with pytest.raises(HTTPException) as excinfo:
        await register_user(user_data, current_user, fake_user_repo)
    assert excinfo.value.status_code == 400


@pytest.mark.asyncio
async def test__unit_test__register_user_error(fake_user_repo):
    user_data = UserCreate(name="error", email="hi@hi.com", scopes=AccessRoles.USER)
    with pytest.raises(HTTPException) as excinfo:
        await register_user(user_data, current_user, fake_user_repo)
    assert excinfo.value.status_code == 500


@pytest.mark.asyncio
async def test__unit_test__register_user_email_error(fake_user_repo, monkeypatch):
    user_data = UserCreate(name="bob", email="hi@hi.com", scopes=AccessRoles.USER)

    # mock email service to raise an error
    async def mock_send_email(*args, **kwargs):
        raise Exception("Email service error")

    class MockEmailService:
        async def send_email(self, *args, **kwargs):
            return await mock_send_email(*args, **kwargs)

    mock_send_email = AsyncMock(side_effect=mock_send_email)
    monkeypatch.setattr("app.routes.user.EmailService", MockEmailService)
    with pytest.raises(HTTPException) as excinfo:
        await register_user(user_data, current_user, fake_user_repo)
    assert excinfo.value.status_code == 500


@pytest.mark.asyncio
async def test__unit_test__get_users(fake_user_repo, monkeypatch):
    result = await get_users(current_user, fake_user_repo)
    assert result == True


@pytest.mark.asyncio
async def test__unit_test__get_users_empty(fake_user_repo, monkeypatch):
    monkeypatch.setattr(fake_user_repo, "get_users", AsyncMock(return_value=None))
    with pytest.raises(HTTPException) as excinfo:
        await get_users(current_user, fake_user_repo)
    assert excinfo.value.status_code == 404


@pytest.mark.asyncio
async def test__unit_test__get_user_me(fake_user_repo, monkeypatch):
    result = await get_user(current_user, fake_user_repo)
    assert result["email"] == current_user["sub"]


@pytest.mark.asyncio
async def test__unit_test__get_user_me_error(fake_user_repo, monkeypatch):
    monkeypatch.setattr(fake_user_repo, "get_by_email", AsyncMock(return_value=None))
    with pytest.raises(HTTPException) as excinfo:
        await get_user(current_user, fake_user_repo)
    assert excinfo.value.status_code == 404


@pytest.mark.asyncio
async def test__unit_test__update_user(fake_user_repo, monkeypatch):
    user_new_data = UserUpdate(
        _id="hi@hi.com",
        password="newpassword",
        is_initialized=True,
        remember_me=True,
        scopes=AccessRoles.USER,
        admin_password="admin_password"
    )


    async def mock_authenticate_user(email, password, repo):
        if email == current_user["sub"]:
            return User()

    monkeypatch.setattr("app.routes.user.authenticate_user", mock_authenticate_user)

    result = await update_user(user_new_data, current_user, fake_user_repo)
    assert result["message"] != None


@pytest.mark.asyncio
async def test__unit_test__update_user_same_data(fake_user_repo, monkeypatch):
    user_new_data = UserUpdate(
        _id="hi3@hi.com",
        password="newpassword",
        is_initialized=True,
        remember_me=True,
        scopes=AccessRoles.USER,
        admin_password="admin_password"
    )

    async def mock_authenticate_user(email, password, repo):
        if email == current_user["sub"]:
            return User()

    monkeypatch.setattr("app.routes.user.authenticate_user", mock_authenticate_user)

    result = await update_user(user_new_data, current_user, fake_user_repo)
    assert result["message"] != None


@pytest.mark.asyncio
async def test__unit_test__update_user_error(fake_user_repo, monkeypatch):
    user_new_data = UserUpdate(
        _id="error@error.com",
        password="newpassword",
        is_initialized=True,
        remember_me=True,
        scopes=AccessRoles.USER,
        admin_password="admin_password"
    )
    with pytest.raises(Exception) as excinfo:
        await update_user(user_new_data, current_user, fake_user_repo)


@pytest.mark.asyncio
async def test__unit_test__update_user_no_edit(fake_user_repo, monkeypatch):
    user_new_data = UserUpdate(
        _id="notfound@error.com",
        password="newpassword",
        is_initialized=True,
        remember_me=True,
        scopes=AccessRoles.USER,
        admin_password="admin_password"
    )

    async def mock_authenticate_user(email, password, repo):
        if email == current_user["sub"]:
            return User()

    monkeypatch.setattr("app.routes.user.authenticate_user", mock_authenticate_user)


    with pytest.raises(HTTPException) as excinfo:
        await update_user(user_new_data, current_user, fake_user_repo)
    assert excinfo.value.status_code == 404


class User:
    def __init__(self):
        self._id = current_user["sub"]

    def get(self, _):
        return self._id


@pytest.mark.asyncio
async def test__unit_test__delete_user(fake_user_repo, monkeypatch):
    delete_user = UserDelete(_id="user123@asd.com")
    admin = UserAuth(current_password="admin_password")

    async def mock_authenticate_user(email, password, repo):
        if email == current_user["sub"]:
            return User()

    monkeypatch.setattr("app.routes.user.authenticate_user", mock_authenticate_user)
    result = await delete_user_fn(delete_user, admin, current_user, fake_user_repo)


@pytest.mark.asyncio
async def test__unit_test__delete_user_no_valid_user(fake_user_repo, monkeypatch):
    delete_user = UserDelete(_id="user123@asd.com")
    admin = UserAuth(current_password="admin_password")

    async def mock_authenticate_user(email, password, repo):
        if email == current_user["sub"]:
            return None

    monkeypatch.setattr("app.routes.user.authenticate_user", mock_authenticate_user)
    user_id = "user123"
    with pytest.raises(HTTPException) as ex:
        result = await delete_user_fn(delete_user, admin, current_user, fake_user_repo)
    assert ex.value.status_code == 401


@pytest.mark.asyncio
async def test__unit_test__delete_user_id_error(fake_user_repo, monkeypatch):
    delete_user = UserDelete(_id="error@asd.com")
    admin = UserAuth(current_password="admin_password")
    current_user = {"sub": "hi2@hi.com"}

    async def mock_authenticate_user(email, password, repo):
        if email == current_user["sub"]:
            return User()

    monkeypatch.setattr("app.routes.user.authenticate_user", mock_authenticate_user)
    with pytest.raises(HTTPException) as ex:
        result = await delete_user_fn(delete_user, admin, current_user, fake_user_repo)
    assert ex.value.status_code == 403


@pytest.mark.asyncio
async def test__unit_test__delete_user_id_jwt_error(fake_user_repo, monkeypatch):
    delete_user = UserDelete(_id="jwterror@asd.com")
    admin = UserAuth(current_password="admin_password")
    current_user = {"sub": "hi@hi.com"}

    async def mock_authenticate_user(email, password, repo):
        if email == current_user["sub"]:
            return User()

    monkeypatch.setattr("app.routes.user.authenticate_user", mock_authenticate_user)
    with pytest.raises(HTTPException) as ex:
        result = await delete_user_fn(delete_user, admin, current_user, fake_user_repo)
    assert ex.value.status_code == 401


@pytest.mark.asyncio
async def test__unit_test__delete_user_exception(fake_user_repo, monkeypatch):
    delete_user = UserDelete(_id="error@asd.com")
    admin = UserAuth(current_password="admin_password")

    async def mock_authenticate_user(email, password, repo):
        if email == current_user["sub"]:
            return User()

    monkeypatch.setattr("app.routes.user.authenticate_user", mock_authenticate_user)
    with pytest.raises(HTTPException) as ex:
        await delete_user_fn(delete_user, admin, current_user, fake_user_repo)
    assert ex.value.status_code == 500


@pytest.mark.asyncio
async def test__unit_test__update_password(fake_user_repo, monkeypatch):
    user_data = UserUpdatePassword(
        password="Abc123!@#@js", current_password="test_password"
    )

    result = await update_password(user_data, current_user, fake_user_repo)
    assert result["message"] != None


@pytest.mark.asyncio
async def test__unit_test__update_password_old_password_error(
    fake_user_repo, monkeypatch
):
    user_data = UserUpdatePassword(
        password="Abc123!@#@js", current_password="test_password2"
    )

    with pytest.raises(HTTPException) as excinfo:
        await update_password(user_data, current_user, fake_user_repo)
    assert excinfo.value.status_code == 500


@pytest.mark.asyncio
async def test__unit_test__update_password_is_not_init_with_not_found(
    fake_user_repo, monkeypatch
):
    user_data = UserUpdatePassword(
        password="Abc123!@#@js", current_password="test_password"
    )
    current_user = {"sub": "hi4@hi.com"}

    with pytest.raises(HTTPException) as excinfo:
        await update_password(user_data, current_user, fake_user_repo)
    assert excinfo.value.status_code == 500


@pytest.mark.asyncio
async def test__unit_test__reset_password(fake_user_repo, monkeypatch):
    user_data = UserForgotPassword(email="hi@hi.com")
    result = await reset_password(user_data, fake_user_repo)
    assert result["message"] != None


@pytest.mark.asyncio
async def test__unit_test__reset_password_not_found(fake_user_repo, monkeypatch):
    user_data = UserForgotPassword(email="notfound@hi.com")
    with pytest.raises(HTTPException) as excinfo:
        await reset_password(user_data, fake_user_repo)
    assert excinfo.value.status_code == 500


@pytest.mark.asyncio
async def test__unit_test__reset_password_update_error(fake_user_repo, monkeypatch):
    user_data = UserForgotPassword(email="hi@hi.com")

    async def mock_update_user(*args, **kwargs):
        raise Exception("Update error")

    monkeypatch.setattr(fake_user_repo, "update_user", mock_update_user)
    with pytest.raises(HTTPException) as excinfo:
        await reset_password(user_data, fake_user_repo)
    assert excinfo.value.status_code == 500


@pytest.mark.asyncio
async def test__unit_test__reset_password_email_error(fake_user_repo, monkeypatch):
    user_data = UserForgotPassword(email="hi@hi.com")

    async def mock_send_email(*args, **kwargs):
        raise Exception("Email service error")

    class MockEmailService:
        async def send_email(self, *args, **kwargs):
            return await mock_send_email(*args, **kwargs)

    mock_send_email = AsyncMock(side_effect=mock_send_email)
    monkeypatch.setattr("app.routes.user.EmailService", MockEmailService)
    result = await reset_password(user_data, fake_user_repo)
    assert result["message"] != None
