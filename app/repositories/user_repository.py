from app.utils import get_password_hash, get_uuid3
import app.schemas as schemas
import uuid


class UserRepository:
    def __init__(self, database):
        self.database = database
        self.collection = database.get_collection("users")

    async def get_by_email(self, email):
        return await self.collection.find_one({"email": email})

    async def create(self, user_data: schemas.User):
        return await self.collection.insert_one(user_data)

    async def add_test_user(self):
        print("Adding test user")
        return await self.collection.insert_one(
            {
                # "_id": get_uuid3("test@test.it"),
                "_id": "test@test.it",
                "hashed_password": get_password_hash("testtest"),
                "is_initialized": False,
                "remember_me": False,
                "scopes": ["user"],
            }
        )

    async def add_test_admin(self):
        print("Adding test admin")
        return await self.collection.insert_one(
            {
                # "_id": get_uuid3("admin@test.it"),
                "_id": "admin@test.it",
                "hashed_password": get_password_hash("adminadmin"),
                "is_initialized": True,
                "remember_me": False,
                "scopes": ["admin"],
            }
        )

    async def get_test_user(self):
        return await self.collection.find_one({"email": "test@test.it"})

    async def get_test_admin(self):
        return await self.collection.find_one({"email": "admin@test.it"})
