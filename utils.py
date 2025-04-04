from passlib.context import CryptContext
import uuid

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