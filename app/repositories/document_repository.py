from app.utils import get_password_hash
import app.schemas as schemas
import uuid
from pymongo.errors import DuplicateKeyError

class DocumentRepository:
	def __init__(self, database):
		self.database = database
		self.collection = database.get_collection("documents")
    
	async def insert_document(self, document: schemas.Document):
		"""
        Inserisce un nuovo documento nel database.
        Il documento viene memorizzato con un UUID generato dal suo percorso file come chiave primaria.
        
        Args:
            document (schemas.Document): L'oggetto documento da inserire.
            
        Returns:
            Il risultato dell'operazione di inserimento.
            
        Raises:
            DuplicateKeyError: Se un documento con lo stesso percorso esiste già.
            Exception: Se si verifica qualsiasi altro errore durante l'inserimento.
        """
		document_data = {
			"_id": str(uuid.uuid3(uuid.NAMESPACE_DNS, document.file_path)),
			"title": document.title,
			"file_path": document.file_path,
			"owner_email": document.owner_email,
			"uploaded_at": document.uploaded_at,
		}
		try:
			return await self.collection.insert_one(document_data)
		except DuplicateKeyError as e:
			print(f"Error inserting document: {e}.")
			raise DuplicateKeyError(f"Error inserting document: {e}.")
		except Exception as e:
			print(f"Error inserting document: {e}")
			raise Exception(f"Error inserting document: {e}")