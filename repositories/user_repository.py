from utils import get_password_hash


class UserRepository:
    def __init__(self, database):
        self.database = database
        self.collection = database.get_collection("users")

    async def get_by_email(self, email):
        return await self.collection.find_one({"email": email})

    async def create(self, user_data):
        return await self.collection.insert_one(user_data)

    async def add_test_user(self):
        print("Adding test user")
        return await self.collection.insert_one(
            {
                "email": "test@test.it",
                "hashed_password": get_password_hash("testtest"),
                "is_initialized": False,
                "scopes": ["user"],
            }
        )

    async def add_test_admin(self):
        print("Adding test admin")
        return await self.collection.insert_one(
            {
                "email": "admin@test.it",
                "hashed_password": get_password_hash("adminadmin"),
                "is_initialized": True,
                "scopes": ["admin"],
            }
        )

    async def get_test_user(self):
        return await self.collection.find_one({"email": "test@test.it"})

    async def get_test_admin(self):
        return await self.collection.find_one({"email": "admin@test.it"})
