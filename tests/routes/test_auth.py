from fastapi.security import OAuth2PasswordRequestForm
import pytest
from httpx import AsyncClient
from fastapi import FastAPI, Depends
from unittest.mock import MagicMock
from app.routes.auth import router as auth_router
from app.repositories.user_repository import UserRepository
from app.schemas import UserUpdate
from app.auth_roles import AccessRoles
from app.utils import verify_password
from fastapi import APIRouter, Depends, HTTPException, status

import os
from datetime import datetime, timedelta
from app.routes.auth import authenticate_user, check_user_initialized,create_access_token,verify_token,oauth2_scheme,verify_user,verify_admin,login_for_access_token,verify_user_token, SECRET_KEY_JWT, ALGORITHM
from jose import JWTError, jwt
@pytest.fixture
def fake_user_repo():
    class FakeUserRepository:
        async def get_by_email(self, email):
            if email == "test@example.com":
                return {
                    "_id": "user123@123.com",
                    "email": email,
                    "hashed_password": "$2b$12$zqt9Rgv1PzORjG5ghJSb6OSdYrt7f7cLc38a21DgX/DMyqt80AUCi",
                    "scopes": ["user"],
                    "remember_me": False,
                    "is_initialized": True,
                }
            elif email == "new@example.com":
                return {
                    "_id": "new@123.com",
                    "email": email,
                    "hashed_password": "$2b$12$zqt9Rgv1PzORjG5ghJSb6OSdYrt7f7cLc38a21DgX/DMyqt80AUCi",
                    "scopes": ["user"],
                    "remember_me": False,
                    "is_initialized": False,
                }
            return None

        async def update_user(self, user_id, user_data):
            return None

    return FakeUserRepository()



@pytest.mark.asyncio
async def test__unit_test__authenticate_user_success(fake_user_repo):
    email = "test@example.com"
    password = "test_password"
    user = await authenticate_user(email, password, fake_user_repo)
    assert user is not None
    assert user["_id"] == "user123@123.com"

@pytest.mark.asyncio
async def test__unit_test__authenticate_user_no_user(fake_user_repo):
    email = "test1@example.com"
    password = "test_password"
    user = await authenticate_user(email, password, fake_user_repo)
    assert user == False

@pytest.mark.asyncio
async def test__unit_test__authenticate_user_wrong_password(fake_user_repo):
    email = "test@example.com"
    password = "wrong_password"
    user = await authenticate_user(email, password, fake_user_repo)
    assert user == False

@pytest.mark.asyncio
async def test__unit_test__check_user_initialized_success(fake_user_repo):
    token = jwt.encode(
        {"sub": "test@example.com"},
        SECRET_KEY_JWT,
        algorithm=ALGORITHM,
    )
    is_initialized = await check_user_initialized(token, fake_user_repo)
    assert is_initialized == True

@pytest.mark.asyncio
async def test__unit_test__check_user_initialized_not_valid_token(fake_user_repo):
    token = jwt.encode(
        {"sub2": "test@example.com"},
        SECRET_KEY_JWT,
        algorithm=ALGORITHM,
    )
    with pytest.raises(HTTPException) as exc_info:
        await check_user_initialized(token, fake_user_repo)
    assert exc_info.value.status_code == 403

@pytest.mark.asyncio
async def test__unit_test__check_user_initialized_not_user_found(fake_user_repo):
    token = jwt.encode(
        {"sub": "test2@example.com"},
        SECRET_KEY_JWT,
        algorithm=ALGORITHM,
    )
    with pytest.raises(HTTPException) as exc_info:
        await check_user_initialized(token, fake_user_repo)
    assert exc_info.value.status_code == 404

@pytest.mark.asyncio
async def test__unit_test__check_user_initialized_jwt_error(fake_user_repo):
    token = jwt.encode(
        {"sub": "test@example.com"},
        "invalid_secret_key",
        algorithm=ALGORITHM,
    )
    with pytest.raises(HTTPException) as exc_info:
        await check_user_initialized(token, fake_user_repo)
    assert exc_info.value.status_code == 403

def test__unit_test__create_access_token():
    data = {"sub": "test@example.com"}
    scopes = ["user"]
    expires_delta = timedelta(minutes=60*24*1024)
    token = create_access_token(data, scopes, expires_delta)
    payload = jwt.decode(token, SECRET_KEY_JWT, algorithms=ALGORITHM)
    assert payload["sub"] == data["sub"]
    assert datetime.fromtimestamp(payload["exp"]) > datetime.now() + timedelta(minutes=59*24*1024)
    assert datetime.fromtimestamp(payload["exp"]) < datetime.now() + timedelta(minutes=61*24*1024)

def test__unit_test__create_access_token_no_exp():
    data = {"sub": "test@example.com"}
    scopes = ["user"]
    token = create_access_token(data, scopes)
    payload = jwt.decode(token, SECRET_KEY_JWT, algorithms=ALGORITHM)
    assert payload["sub"] == data["sub"]
    assert datetime.fromtimestamp(payload["exp"]) > datetime.now() + timedelta(minutes=59*24)
    assert datetime.fromtimestamp(payload["exp"]) < datetime.now() + timedelta(minutes=61*24)

def test__unit_test__verify_token():
    data = {"sub": "test@example.com"}
    token = create_access_token(data, AccessRoles.USER)
    payload = verify_token(token, AccessRoles.USER)
    assert payload["sub"] == data["sub"]

def test__unit_test__verify_token_no_email():
    data = {"sub2": "test@example.com"}
    token = create_access_token(data, AccessRoles.USER)
    with pytest.raises(HTTPException) as exc_info:
        verify_token(token, AccessRoles.USER)
    assert exc_info.value.status_code == 403

def test__unit_test__verify_token_no_scope():
    data = {"sub": "test@example.com"}
    token = create_access_token(data, AccessRoles.USER)
    with pytest.raises(HTTPException) as exc_info:
        verify_token(token, AccessRoles.ADMIN)
    assert exc_info.value.status_code == 403

def test__unit_test__verify_token_jwt_error():
    data = {"sub": "123"}
    token = jwt.encode(data, "invalid_secret_key", algorithm=ALGORITHM)
    with pytest.raises(HTTPException) as exc_info:
        verify_token(token, AccessRoles.USER)
    assert exc_info.value.status_code == 403


def test__unit_test__verify_user():
    data = {"sub": "123"}
    token = create_access_token(data, AccessRoles.USER)
    result = verify_user(token)
    assert result["sub"] == data["sub"]

def test__unit_test__verify_admin():
    data = {"sub": "123"}
    token = create_access_token(data, AccessRoles.ADMIN)
    result = verify_admin(token)
    assert result["sub"] == data["sub"]


@pytest.mark.asyncio
async def test__unit_test__login_for_access_token_success(fake_user_repo):
    form_data = OAuth2PasswordRequestForm(username="test@example.com",password="test_password")
    remember_me = False

    response = await login_for_access_token(form_data, remember_me, fake_user_repo)
    assert response["access_token"] is not None
    assert response["token_type"] == "bearer"
    assert response["expires_in"] == None

@pytest.mark.asyncio
async def test__unit_test__login_for_access_token_not_user_or_wrong_password(fake_user_repo):
    form_data = OAuth2PasswordRequestForm(username="test2@example.com",password="test2_password")
    remember_me = False
    with pytest.raises(HTTPException) as exc_info:
        await login_for_access_token(form_data, remember_me, fake_user_repo)
    assert exc_info.value.status_code == 401



@pytest.mark.asyncio
async def test__unit_test__login_for_access_token_success_update_remenber_me(fake_user_repo):
    form_data = OAuth2PasswordRequestForm(username="test@example.com",password="test_password")
    remember_me = True
    await login_for_access_token(form_data, remember_me, fake_user_repo)
    response = await login_for_access_token(form_data, remember_me, fake_user_repo)
    assert response["access_token"] is not None
    assert response["token_type"] == "bearer"
    assert response["expires_in"] != None



@pytest.mark.asyncio
async def test__unit_test__verify_user_token_valid(fake_user_repo):
    token = jwt.encode(
        {"sub": "test@example.com"},
        SECRET_KEY_JWT,
        algorithm=ALGORITHM,
    )
    user = await verify_user_token(token, fake_user_repo)
    assert user is not None
    assert user["status"] == "valid"

@pytest.mark.asyncio
async def test__unit_test__verify_user_token_no_init(fake_user_repo):
    token = jwt.encode(
        {"sub": "new@example.com"},
        SECRET_KEY_JWT,
        algorithm=ALGORITHM,
    )
    user = await verify_user_token(token, fake_user_repo)
    assert user is not None
    assert user["status"] == "not_initialized"



