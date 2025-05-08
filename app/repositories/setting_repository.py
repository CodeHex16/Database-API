from fastapi import Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.database import get_db
from app.schemas import Settings


def get_setting_repository(db: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Restituisce il repository della collection settings.
    """
    return SettingRepository(db)


class SettingRepository:
    def __init__(self, database):
        self.database = database
        self.collection = database.get_collection("settings")

        insert_payload = {
                "color_primary": "#5e5c64",
                "color_primary_hover": "#44424a",
                "color_primary_text": "white",
                "message_history": 100,
        }
        self.collection.update_one(
            {"_id": "main"},
            { 
                "$set": insert_payload,
            },
            upsert=True,
        )

    async def get_settings(self):
        """
        Restituisce le impostazioni dell'applicazione.
        """
        return await self.collection.find_one({"_id": "main"})

    async def update_settings(self, settings: Settings):
        """
        Aggiorna le impostazioni dell'applicazione.
        """
        try:
            current_settings = await self.get_settings()

            if not current_settings:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Settings not found",
                )

            # Controlla se le impostazioni sono state modificate
            if (
                current_settings.get("color_primary") == settings.color_primary
                and current_settings.get("color_primary_hover")
                == settings.color_primary_hover
                and current_settings.get("color_primary_text")
                == settings.color_primary_text
                and current_settings.get("message_history") == settings.message_history
            ):
                print("Settings data is already up to date.")
                raise HTTPException(
                    status_code=status.HTTP_304_NOT_MODIFIED,
                    detail="Settings data is already up to date.",
                )

            # Prepara il payload di aggiornamento
            update_payload = {
                "color_primary": (
                    settings.color_primary
                    if settings.color_primary
                    else current_settings.get("color_primary")
                ),
                "color_primary_hover": (
                    settings.color_primary_hover
                    if settings.color_primary_hover
                    else current_settings.get("color_primary_hover")
                ),
                "color_primary_text": (
                    settings.color_primary_text
                    if settings.color_primary_text
                    else current_settings.get("color_primary_text")
                ),
                "message_history": (
                    settings.message_history
                    if settings.message_history
                    else current_settings.get("message_history")
                ),
            }

            result = await self.collection.update_one(
                {"_id": "main"},
                {
                    "$set": update_payload,
                },
            )

            # Controlla se l'aggiornamento ha avuto effetto
            if result.matched_count == 0:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Settings not found during update attempt",
                )
        except Exception as e:
            print(f"Error updating settings: {e}")
            raise Exception(f"Error updating settings: {e}")
