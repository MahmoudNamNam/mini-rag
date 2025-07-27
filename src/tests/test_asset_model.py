import pytest
from unittest.mock import AsyncMock, patch
from bson import ObjectId
from models.AssetModel import AssetModel
from models.db_schemes import Asset
from helper.config import Settings


# إعداد مزيف للـ settings (بديل للـ .env)
@pytest.fixture
def fake_settings():
    return Settings(
        APP_NAME="TestApp",
        APP_VERSION="0.1",
        APP_DESCRIPTION="Test mode",
        FILE_ALLOWED_TYPES=["application/pdf"],
        FILE_MAX_SIZE=10,
        FILE_DEFAULT_CHUNK_SIZE=512000,
        MONGO_URI="mongodb://localhost:27017",
        MONGO_DB_NAME="test_db"
    )


@pytest.fixture
def fake_db_client():
    collection = AsyncMock()
    db = {"assets": collection}
    client = AsyncMock()
    client.__getitem__.side_effect = lambda name: db if name == "test_db" else db[name]
    return client


@pytest.mark.asyncio
@patch("models.BaseDataModel.get_settings")
async def test_create_asset(mock_get_settings, fake_db_client, fake_settings):
    mock_get_settings.return_value = fake_settings

    asset_model = AssetModel(db_client=fake_db_client)
    fake_db_client["test_db"]["assets"].insert_one.return_value.inserted_id = ObjectId()

    asset = Asset(
        asset_project_id=ObjectId(),
        asset_name="test.pdf",
        asset_type="pdf"
    )

    result = await asset_model.create_asset(asset)

    assert result.id is not None
    fake_db_client["test_db"]["assets"].insert_one.assert_awaited_once()


@pytest.mark.asyncio
@patch("models.BaseDataModel.get_settings")
async def test_get_asset_record_found(mock_get_settings, fake_db_client, fake_settings):
    mock_get_settings.return_value = fake_settings
    test_project_id = ObjectId()

    fake_db_client["test_db"]["assets"].find_one.return_value = {
        "_id": ObjectId(),
        "asset_project_id": test_project_id,
        "asset_name": "doc.pdf",
        "asset_type": "pdf"
    }

    asset_model = AssetModel(db_client=fake_db_client)
    asset = await asset_model.get_asset_record(str(test_project_id), "doc.pdf")

    assert asset.asset_name == "doc.pdf"
    fake_db_client["test_db"]["assets"].find_one.assert_awaited_once()
