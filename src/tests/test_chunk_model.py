import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from bson import ObjectId
from models.ChunkModel import ChunkModel
from models.db_schemes import DataChunk
from models.enums.DataBaseEnum import DataBaseEnum
from helper.config import Settings

@pytest.fixture
def fake_settings():
    return Settings(
        APP_NAME="test",
        APP_VERSION="0.1",
        APP_DESCRIPTION="desc",
        FILE_ALLOWED_TYPES=["application/pdf"],
        FILE_MAX_SIZE=10,
        FILE_DEFAULT_CHUNK_SIZE=100,
        MONGO_URI="mongodb://localhost",
        MONGO_DB_NAME="test_db"
    )

@pytest.fixture
def fake_db_client():
    return AsyncMock()

@patch("models.BaseDataModel.get_settings")
@pytest.mark.asyncio
async def test_init_collection(mock_get_settings, fake_db_client, fake_settings):
    mock_get_settings.return_value = fake_settings

    db = AsyncMock()
    db.list_collection_names.return_value = []
    fake_db_client.__getitem__.return_value = db

    model = await ChunkModel.create_instance(db_client=fake_db_client)

    db.list_collection_names.assert_awaited_once()
    assert model.collection is not None

@patch("models.BaseDataModel.get_settings")
@pytest.mark.asyncio
async def test_create_chunk(mock_get_settings, fake_db_client, fake_settings):
    mock_get_settings.return_value = fake_settings

    mock_collection = AsyncMock()
    fake_db_client.__getitem__.return_value = {DataBaseEnum.COLLECTION_CHUNK_NAME.value: mock_collection}
    model = ChunkModel(db_client=fake_db_client)
    model.collection = mock_collection

    chunk = DataChunk(
        chunk_text="hello",
        chunk_metadata={"source": "test"},
        chunk_order=1,
        chunk_project_id=ObjectId(),
        chunk_asset_id=ObjectId()
    )

    mock_collection.insert_one.return_value.inserted_id = ObjectId()
    result = await model.create_chunk(chunk)

    assert result.id is not None
    mock_collection.insert_one.assert_awaited_once()

@patch("models.BaseDataModel.get_settings")
@pytest.mark.asyncio
async def test_get_chunk(mock_get_settings, fake_db_client, fake_settings):
    mock_get_settings.return_value = fake_settings

    mock_collection = AsyncMock()
    fake_db_client.__getitem__.return_value = {DataBaseEnum.COLLECTION_CHUNK_NAME.value: mock_collection}
    model = ChunkModel(db_client=fake_db_client)
    model.collection = mock_collection

    fake_id = ObjectId()
    fake_chunk = {
        "_id": fake_id,
        "chunk_text": "data",
        "chunk_metadata": {},
        "chunk_order": 1,
        "chunk_project_id": ObjectId(),
        "chunk_asset_id": ObjectId()
    }
    mock_collection.find_one.return_value = fake_chunk

    result = await model.get_chunk(str(fake_id))
    assert result.chunk_text == "data"
    mock_collection.find_one.assert_awaited_once()

@patch("models.BaseDataModel.get_settings")
@pytest.mark.asyncio
async def test_insert_many_chunks(mock_get_settings, fake_db_client, fake_settings):
    mock_get_settings.return_value = fake_settings

    mock_collection = AsyncMock()
    fake_db_client.__getitem__.return_value = {DataBaseEnum.COLLECTION_CHUNK_NAME.value: mock_collection}
    model = ChunkModel(db_client=fake_db_client)
    model.collection = mock_collection

    chunks = [
        DataChunk(
            chunk_text=f"text {i}",
            chunk_metadata={},
            chunk_order=i + 1,
            chunk_project_id=ObjectId(),
            chunk_asset_id=ObjectId()
        )
        for i in range(5)
    ]

    await model.insert_many_chunks(chunks, batch_size=2)
    assert mock_collection.bulk_write.await_count == 3

@patch("models.BaseDataModel.get_settings")
@pytest.mark.asyncio
async def test_delete_chunk_by_project_id(mock_get_settings, fake_db_client, fake_settings):
    mock_get_settings.return_value = fake_settings

    mock_collection = AsyncMock()
    fake_db_client.__getitem__.return_value = {DataBaseEnum.COLLECTION_CHUNK_NAME.value: mock_collection}
    model = ChunkModel(db_client=fake_db_client)
    model.collection = mock_collection

    mock_collection.delete_many.return_value.deleted_count = 5

    result = await model.delete_chunk_by_project_id(ObjectId())
    assert result == 5
    mock_collection.delete_many.assert_awaited_once()
