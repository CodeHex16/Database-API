from fastapi import APIRouter, Depends, HTTPException, status

import app.schemas as schemas
from app.routes.auth import verify_admin
from app.repositories.setting_repository import (
    SettingRepository,
    get_setting_repository,
)

router = APIRouter(prefix="/settings", tags=["setting"])


@router.get(
    "",
    response_model=schemas.Settings,
)
async def get_settings(
    setting_repository: SettingRepository = Depends(get_setting_repository),
):
    """
    Restituisce le impostazioni dell'applicazione.

    ### Returns:
    * **schemas.Settings**: Le impostazioni dell'applicazione.

    ### Raises:
    * **HTTPException.HTTP_404_NOT_FOUND**: Se le impostazioni non sono state trovate.
    * **HTTPException.HTTP_500_INTERNAL_SERVER_ERROR**: Se si verifica un errore durante il recupero delle impostazioni.
    """
    try:
        settings = await setting_repository.get_settings()
        if not settings:
            raise HTTPException(
                status_code=404,
                detail="Settings not found",
            )
        return settings
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving settings: {str(e)}",
        )


@router.patch(
    "",
)
async def update_settings(
    settings: schemas.Settings,
    current_user=Depends(verify_admin),
    setting_repository: SettingRepository = Depends(get_setting_repository),
):
    """
    Aggiorna le impostazioni dell'applicazione.

    ### Args:
    * **settings**: Le impostazioni da aggiornare.

    ### Raises:
    * **HTTPException.HTTP_401_UNAUTHORIZED**: Se l'utente non è autorizzato a compiere questa azione.
    * **HTTPException.HTTP_500_INTERNAL_SERVER_ERROR**: Se si verifica un errore durante l'aggiornamento delle impostazioni.
    * **HTTPException.HTTP_304_NOT_MODIFIED**: Se le impostazioni non sono state modificate.
    * **HTTPException.HTTP_404_NOT_FOUND**: Se le impostazioni non sono state trovate.
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authorized",
        )

    try:
        await setting_repository.update_settings(settings)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating settings: {str(e)}",
        )
