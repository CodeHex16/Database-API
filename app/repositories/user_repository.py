import uuid
from fastapi import HTTPException, status, Depends
from pydantic import EmailStr
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from app.database import get_db


from app.utils import get_password_hash, verify_password
import app.schemas as schemas


class UserRepository:
    def __init__(self, database):
        self.database = database
        self.collection = database.get_collection("users")

    async def get_users(self):
        return await self.collection.find().to_list(length=None)

    async def get_by_email(self, user_id: EmailStr):
        return await self.collection.find_one({"_id": user_id})

    async def create_user(self, user_data: schemas.User):
        return await self.collection.insert_one(user_data)

    async def add_test_user(self):
        print("Adding test user")
        try:
            return await self.collection.insert_one(
                {
                    # "_id": get_uuid3("test@test.it"),
                    "_id": "test@test.it",
                    "name": "Test User",
                    "hashed_password": get_password_hash("testtest"),
                    "is_initialized": False,
                    "remember_me": False,
                    "scopes": ["user"],
                }
            )
        except Exception as e:
            print(f"Error adding test user: {e}")
            return None

    async def add_test_admin(self):
        print("Adding test admin")
        try:
            return await self.collection.insert_one(
                {
                    # "_id": get_uuid3("admin@test.it"),
                    "_id": "admin@test.it",
                    "name": "Test Admin",
                    "hashed_password": get_password_hash("adminadmin"),
                    "is_initialized": True,
                    "remember_me": False,
                    "scopes": ["admin"],
                }
            )
        except Exception as e:
            print(f"Error adding test admin: {e}")
            return None

    async def get_test_user(self):
        return await self.collection.find_one({"email": "test@test.it"})

    async def get_test_admin(self):
        return await self.collection.find_one({"email": "admin@test.it"})

    async def delete_user(self, user_id: EmailStr):
        """
        Elimina un utente dal database in base all'email fornita.
        Args:
            user_email (str): L'email dell'utente da eliminare.
        Returns:
            Il risultato dell'operazione di eliminazione.
        """
        # Elimina l'utente dal database using the injected repository
        try:
            result = await self.collection.delete_one({"_id": user_id})
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete user: {e}",
            )

        if result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

    async def update_user(self, user_id: EmailStr, user_data: schemas.UserUpdate):
        """
        Aggiorna un utente esistente nel database.
        Args:
            user_id (EmailStr): L'email (_id) dell'utente da aggiornare.
            user_data (schemas.UserUpdate): I nuovi dati dell'utente.
        Returns:
            UpdateResult: The result of the update operation, or None if no changes were made.
        Raises:
            HTTPException: If user not found (404) or if provided data matches existing (304).
        """
        # Controlla se l'utente esiste
        user_current_data = await self.get_by_email(user_id)
        if not user_current_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
  
        # Prepara il payload di aggiornamento
        update_payload = {}
        if user_data.password is not None:
            if not verify_password(
                user_data.password, user_current_data.get("hashed_password")
            ):
                update_payload["hashed_password"] = get_password_hash(
                    user_data.password
                )
        if (
            user_data.is_initialized is not None
            and user_data.is_initialized != user_current_data.get("is_initialized")
        ):
            update_payload["is_initialized"] = user_data.is_initialized
        if (
            user_data.remember_me is not None
            and user_data.remember_me != user_current_data.get("remember_me")
        ):
            update_payload["remember_me"] = user_data.remember_me
        if user_data.scopes is not None and user_data.scopes != user_current_data.get(
            "scopes"
        ):
            update_payload["scopes"] = user_data.scopes

        # Controlla se ci sono stati cambiamenti nei dati
        if not update_payload:
            provided_data = user_data.model_dump(exclude_unset=True)
            if provided_data:
                raise HTTPException(
                    status_code=status.HTTP_304_NOT_MODIFIED,
                    detail="User data provided matches existing data. No update performed.",
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No data provided for update.",
                )

        try:
            result = await self.collection.update_one(
                {"_id": user_id}, {"$set": update_payload}
            )
            return result
        except Exception as e:
            print(f"Error updating user in repository: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update user: {e}",
            )

def get_user_repository(db: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Restituisce il repository della collection users.
    """
    return UserRepository(db)
