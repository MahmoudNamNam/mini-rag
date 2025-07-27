import pytest
from unittest.mock import AsyncMock, patch
from bson import ObjectId
from models.ProjectModel import ProjectModel
from models.db_schemes import Project

@pytest.fixture
def fake_db_client():
    return AsyncMock()

@pytest.fixture
def fake_settings():
    return Project(project_id="test123")

@pytest.mark.asyncio
@patch("models.BaseDataModel.get_settings")
async def test_create_project(mock_get_settings, fake_db_client, fake_settings):
    mock_collection = AsyncMock()
    fake_db_client.__getitem__.return_value = {"projects": mock_collection}
    mock_collection.insert_one.return_value.inserted_id = ObjectId("64f07e1cfc13ae1c4b000000")

    mock_get_settings.return_value.MONGO_DB_NAME = "test_db"

    project_model = ProjectModel(db_client=fake_db_client)
    result = await project_model.create_project(fake_settings)

    assert result.id == ObjectId("64f07e1cfc13ae1c4b000000")

@pytest.mark.asyncio
@patch("models.BaseDataModel.get_settings")
async def test_get_project_or_create_new(mock_get_settings, fake_db_client):
    mock_collection = AsyncMock()
    fake_db_client.__getitem__.return_value = {"projects": mock_collection}

    mock_collection.find_one.return_value = None
    mock_collection.insert_one.return_value.inserted_id = ObjectId("64f07e1cfc13ae1c4b000111")
    mock_get_settings.return_value.MONGO_DB_NAME = "test_db"

    model = ProjectModel(db_client=fake_db_client)
    project = await model.get_project_or_create_one("auto123")

    assert project.project_id == "auto123"
    assert project.id == ObjectId("64f07e1cfc13ae1c4b000111")

@pytest.mark.asyncio
@patch("models.BaseDataModel.get_settings")
async def test_get_all_projects(mock_get_settings, fake_db_client):
    mock_collection = AsyncMock()
    fake_db_client.__getitem__.return_value = {"projects": mock_collection}

    project_doc = {"_id": ObjectId(), "project_id": "p1"}
    mock_collection.count_documents.return_value = 1

    mock_cursor = AsyncMock()
    mock_cursor.skip.return_value.limit.return_value.__aiter__.return_value = [project_doc]
    mock_collection.find.return_value = mock_cursor

    mock_get_settings.return_value.MONGO_DB_NAME = "test_db"

    model = ProjectModel(db_client=fake_db_client)
    projects, total_pages = await model.get_all_projects(page=1, page_size=10)

    assert len(projects) == 1
    assert projects[0].project_id == "p1"
    assert total_pages == 1
