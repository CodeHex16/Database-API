from utils import get_password_hash
import schemas

class DocumentRepository:
	def __init__(self, database):
		self.database = database
		self.collection = database.get_collection("documents")
    
	async def insert_document(self, document: schemas.Document):
		return await self.collection.insert_one(document.model_dump())