import os

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    PYTHONDONTWRITEBYTECODE = 1

class TestingConfig:
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL_TEST')
    TESTING = True
