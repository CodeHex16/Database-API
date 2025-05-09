import pytest

from unittest.mock import MagicMock, AsyncMock, patch


from app.database import get_db, init_db

@pytest.mark.asyncio
async def test__unit_test__get_database_error():
    with pytest.raises(RuntimeError):
        await get_db()

@pytest.mark.asyncio
async def test__unit_test__get_database():
    mock_db = MagicMock()
    init_db(mock_db)
    db = await get_db()
    assert db == mock_db


