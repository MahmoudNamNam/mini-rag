import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from models.BaseDataModel import BaseDataModel
from helper.config import Settings


@pytest.fixture
def fake_settings():
    return Settings(
        APP_NAME="Test",
        APP_VERSION="1.0",
        APP_DESCRIPTION="testing",
        FILE_ALLOWED_TYPES=["application/pdf"],
        FILE_MAX_SIZE=10,
        FILE_DEFAULT_CHUNK_SIZE=1000,
        MONGO_URI="mongodb://localhost",
        MONGO_DB_NAME="test_db"
    )


@pytest.mark.asyncio
@patch("models.BaseDataModel.get_settings")
async def test_init_collection_with_indexes_creates_new_collection(mock_get_settings, fake_settings):
    # Arrange
    mock_get_settings.return_value = fake_settings

    # mock MongoDB
    mock_collection = AsyncMock()
    mock_db = {
        "test_collection": mock_collection
    }
    mock_db_obj = AsyncMock()
    mock_db_obj.__getitem__.side_effect = lambda name: mock_collection
    mock_db_obj.list_collection_names.return_value = []

    mock_client = MagicMock()
    mock_client.__getitem__.return_value = mock_db_obj

    # setup model
    model = BaseDataModel(db_client=mock_client)

    # test index list
    indexes = [
        {
            "key": [("field1", 1)],
            "name": "field1_index",
            "unique": True
        }
    ]

    # Act
    await model.init_collection_with_indexes("test_collection", indexes)

    # Assert
    mock_collection.create_index.assert_awaited_once_with(
        indexes[0]["key"], name="field1_index", unique=True
    )
