class UserRepository:
    def __init__(self, database):
        self.database = database
        self.collection = database.get_collection("users")
        
    async def get_by_email(self, email):
        return await self.collection.find_one({"email": email})
        
    async def create(self, user_data):
        return await self.collection.insert_one(user_data)