import pytest

from app.utils import get_password_hash, verify_password, get_uuid3, get_object_id, get_timezone

def test__unit_test__get_password_hash():
    password = "test_password"
    hashed_password = get_password_hash(password)
    assert hashed_password != password
    assert hashed_password.startswith("$2b$12$")

def test__unit_test__verify_password():
    password = "test_password"
    hashed_password = "$2b$12$zqt9Rgv1PzORjG5ghJSb6OSdYrt7f7cLc38a21DgX/DMyqt80AUCi"
    assert verify_password(password, hashed_password) == True
    assert verify_password("wrong_password", hashed_password) == False

def test__unit_test__get_uuid3():
    text = "test_text"
    expected_uuid = "512a1046-d071-3411-8219-545197d8c9fb"
    assert get_uuid3(text) == expected_uuid
    assert get_uuid3("another_text") != expected_uuid

def test__unit_test__get_object_id():
    text = "test_text"
    expected_object_id = "3bac26ca6ad022ede83faa58"
    assert str(get_object_id(text)) == expected_object_id
    assert str(get_object_id("another_text")) != expected_object_id

def test__unit_test__get_timezone():
    expected_timezone = "Europe/Rome"
    assert get_timezone().zone == expected_timezone