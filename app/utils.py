from passlib.context import CryptContext
import uuid
import pytz
import hashlib
from bson import ObjectId


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password):
    return pwd_context.hash(password)


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_uuid3(text):
    """
    Generate a UUID3 hash from the given text.
    """
    return str(uuid.uuid3(uuid.NAMESPACE_DNS, text))

def get_object_id(text):
    hash_bytes = hashlib.md5(text.encode('utf-8')).digest()[:12]
    return ObjectId(hash_bytes)

def get_timezone():
    """
    Get the timezone of the server.
    """
    return pytz.timezone("Europe/Rome")
