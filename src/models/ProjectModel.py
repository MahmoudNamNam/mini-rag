import logging
from .BaseDataModel import BaseDataModel
from .db_schemes import Project
from .enums.DataBaseEnum import DataBaseEnum
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.future import select
from sqlalchemy import func


logger = logging.getLogger(__name__)

class ProjectModel(BaseDataModel):

    def __init__(self, db_client: object):
        super().__init__(db_client=db_client)
        self.db_client = db_client


    @classmethod
    async def create_instance(cls, db_client: object):
        instance = cls(db_client=db_client)
        return instance



    async def create_project(self, project: Project) -> Project:
        logger.info("Attempting to create project with ID: %s", project.project_id)

        async with self.db_client() as session:
            try:
                async with session.begin():
                    session.add(project)
                    await session.flush()
                    await session.refresh(project)
                    logger.info("Project created successfully with ID: %s", project.project_id)
                    return project
            except SQLAlchemyError as e:
                logger.exception("Failed to create project with ID %s: %s", project.project_id, str(e))
                raise


    async def get_project_or_create_one(self, project_id: int) -> Project:
        logger.info("Looking for project with ID: %s", project_id)

        async with self.db_client() as session:
            try:
                async with session.begin():
                    query = select(Project).where(Project.project_id == project_id)
                    result = await session.execute(query)
                    project_record = result.scalar_one_or_none()

                    if project_record:
                        logger.info("Project found with ID: %s", project_id)
                        return project_record

            except SQLAlchemyError as e:
                logger.exception("Error during project lookup by ID %s: %s", project_id, str(e))
                raise
        logger.info("Project with ID %s not found. Creating a new one.", project_id)
        # If project wasn't found, create a new one outside the previous session context
        new_project = Project(project_id=project_id)
        return await self.create_project(new_project)

    async def get_all_projects(self, page: int = 1, page_size: int = 10):
        # Validate page & page_size
        if page < 1:
            page = 1
        if page_size < 1 or page_size > 100:
            page_size = 10

        logger.info("Fetching all projects: page %d with page size %d", page, page_size)

        async with self.db_client() as session:
            try:
                async with session.begin():
                    # Count total number of projects
                    total_count_result = await session.execute(select(func.count(Project.project_id)))
                    total_documents = total_count_result.scalar_one()

                    total_pages = (total_documents + page_size - 1) // page_size
                    offset = (page - 1) * page_size
                    
                    # Fetch paginated data
                    query = select(Project).offset(offset).limit(page_size)
                    result = await session.execute(query)
                    projects = result.scalars().all()

                    return {
                        "total_documents": total_documents,
                        "total_pages": total_pages,
                        "current_page": page,
                        "page_size": page_size,
                        "projects": projects
                    }

            except SQLAlchemyError as e:
                logger.exception("Error fetching projects: %s", str(e))
                raise
