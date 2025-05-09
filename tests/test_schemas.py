import pytest
from pydantic import ValidationError
from app.schemas import (
    _ObjectIdPydanticAnnotation,
    EmailSchema,
    UserUpdatePassword,
    FAQ,
    FAQUpdate,
    FAQResponse,
    DocumentResponse,
)


##########################################################################################
# USER SCHEMA TESTS
def test__unit_test__valid_email_list():
    data = {"email": ["test@example.com", "hello@world.com"]}
    schema = EmailSchema(**data)
    assert schema.email == data["email"]

def test__unit_test__invalid_email_format():
    with pytest.raises(ValidationError):
        EmailSchema(email=["invalid-email", "test@example.com"])

def test__unit_test__empty_email_list():
    schema = EmailSchema(email=[])
    assert schema.email == []

def test__unit_test__missing_email_field():
    with pytest.raises(ValidationError):
        EmailSchema()

############################################################################################
# USER UPDATE PASSWORD SCHEMA TESTS
def test__unit_test__valid_user_update_password():
    data = {
        "password": "ValidPassword123!",
        "current_password": "CurrentPassword123!"
    }
    schema = UserUpdatePassword(**data)
    assert schema.password == data["password"]
    assert schema.current_password == data["current_password"]

def test__unit_test__invalid_user_update_password():
    with pytest.raises(ValidationError):
        UserUpdatePassword(password="short", current_password="short")

def test__unit_test__missing_user_update_password_fields():
    with pytest.raises(ValidationError):
        UserUpdatePassword()

def test__unit_test__password_regex_tests():
    valid_passwords = [
        "Abcdef1!",         # minimal valid
        "Str0ng@Pass",      # common format
        "GoodDay#2024",     # year + symbol
        "My_Passw0rd!",     # underscore & symbol
        "T3stP@ssword",     # mixed characters
        "Welc0me$Home",     # readable phrase
        "A1b2C3d4!",        # repeated pattern
        "Zz9#Zz9#",         # symmetric pattern
        "Python@123",       # tech themed
        "Valid123!",        # clear and simple
        "U!uU!uU!1",        # complex mix
        "PassWord1*"        # typical strong password
    ]

    invalid_passwords = [
        "abcdefg",          # no uppercase, digit, or special
        "ABCDEFGH",         # no lowercase, digit, or special
        "12345678",         # only digits
        "password",         # lowercase only
        "PASSWORD",         # uppercase only
        "Pass1234",         # missing special character
        "P@ssword",         # missing digit
        "1234@ABC",         # missing lowercase
        "Short1!",          # only 7 characters
        "NoSpecChar1",      # missing special character
    ]

    # Testing valid passwords
    for password in valid_passwords:
        schema = UserUpdatePassword(password=password, current_password="CurrentPassword123!")
        assert schema.password == password
        assert schema.current_password == "CurrentPassword123!"

    # Testing invalid passwords
    for password in invalid_passwords:
        with pytest.raises(ValidationError):
            UserUpdatePassword(password=password, current_password="CurrentPassword123!")

#########################################################################################
# FAQ SCHEMA TESTS
def test___unit_test__invalide_faq_title_length():
    with pytest.raises(ValidationError):
        FAQ(title="a" * 31, question="What is this?", answer="This is a test answer.")

def test__unit_test__valid_faq_title_length():
    data = {
        "title": "Valid Title",
        "question": "What is this?",
        "answer": "This is a test answer."
    }
    schema = FAQ(**data)
    assert schema.title == data["title"]
    assert schema.question == data["question"]
    assert schema.answer == data["answer"]


###################################################################################
# FAQ UPDATE SCHEMA TESTS
def test__unit_test__valid_faq_update():
    data = {
        "title": "Updated Title",
        "question": "What is this?",
        "answer": "This is a test answer."
    }
    schema = FAQUpdate(**data)
    assert schema.title == data["title"]
    assert schema.question == data["question"]
    assert schema.answer == data["answer"]

def test__unit_test__invalid_faq_update_title_length():
    with pytest.raises(ValidationError):
        FAQUpdate(title="a" * 31, question="What is this?", answer="This is a test answer.")
