import logging
from .BaseDataModel import BaseDataModel
from .db_schemes import Project
from .enums.DataBaseEnum import DataBaseEnum

# Configure logger for this module
logger = logging.getLogger(__name__)

class ProjectModel(BaseDataModel):

    def __init__(self, db_client: object):
        super().__init__(db_client=db_client)
        self.collection = self.db_client[DataBaseEnum.DATABASE_NAME.value][DataBaseEnum.COLLECTION_PROJECT_NAME.value]

        logger.info("ProjectModel initialized with collection: %s", self.collection.name)

    async def create_project(self, project: Project):
        logger.info("Attempting to create project with ID: %s", project.project_id)
        try:
            result = await self.collection.insert_one(project.dict(by_alias=True, exclude_unset=True))
            project._id = result.inserted_id
            logger.info("Project created successfully with ObjectId: %s", result.inserted_id)
            return project
        except Exception as e:
            logger.exception("Failed to create project with ID %s: %s", project.project_id, str(e))
            raise

    async def get_project_or_create_one(self, project_id: str):
        logger.info("Looking for project with ID: %s", project_id)

        record = await self.collection.find_one({"project_id": project_id})

        if record is None:
            logger.info("Project with ID %s not found. Creating a new one.", project_id)
            try:
                project = Project(project_id=project_id)
                project = await self.create_project(project=project)
                return project
            except Exception as e:
                logger.exception("Failed to create new project with ID %s: %s", project_id, str(e))
                raise
        else:
            logger.info("Found existing project with ID: %s", project_id)
            return Project(**record)

    async def get_all_projects(self, page: int = 1, page_size: int = 10):
        logger.info("Fetching all projects: page %d with page size %d", page, page_size)
        try:
            total_documents = await self.collection.count_documents({})
            total_pages = (total_documents + page_size - 1) // page_size

            cursor = self.collection.find().skip((page - 1) * page_size).limit(page_size)
            projects = [Project(**document) async for document in cursor]

            logger.info("Fetched %d projects (page %d of %d)", len(projects), page, total_pages)
            return projects, total_pages
        except Exception as e:
            logger.exception("Failed to fetch projects: %s", str(e))
            raise
