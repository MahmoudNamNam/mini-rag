import logging
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from .BaseDataModel import BaseDataModel
from .db_schemes import Asset
from typing import List, Optional

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

class AssetModel(BaseDataModel):
    def __init__(self, db_client: object):
        super().__init__(db_client=db_client)
        self.db_client = db_client

    @classmethod
    async def create_instance(cls, db_client: object):
        return cls(db_client=db_client)

    async def create_asset(self, asset: Asset) -> Asset:
        logger.info("Attempting to create asset of name: %s", asset.asset_name)
        async with self.db_client() as session:
            try:
                async with session.begin():
                    session.add(asset)
                    await session.flush()
                    await session.refresh(asset)
                    logger.info("Asset created successfully with ID: %s", asset.asset_id)
                    return asset
            except SQLAlchemyError as e:
                logger.exception("Failed to create asset: %s", str(e))
                raise

    async def get_all_project_assets(self, asset_project_id: int, asset_type: str) -> List[Asset]:
        logger.info("Fetching all assets for project_id: %s with type: %s", asset_project_id, asset_type)
        async with self.db_client() as session:
            try:
                async with session.begin():
                    query = select(Asset).where(
                        Asset.asset_project_id == asset_project_id,
                        Asset.asset_type == asset_type
                    )
                    result = await session.execute(query)
                    assets = result.scalars().all()
                    logger.info("Found %d assets for project_id: %s", len(assets), asset_project_id)
                    return assets
            except SQLAlchemyError as e:
                logger.exception("Failed to fetch assets: %s", str(e))
                raise

    async def get_asset_record(self, asset_project_id: int, asset_name: str) -> Optional[Asset]:
        logger.info("Looking up asset with name '%s' in project_id: %s", asset_name, asset_project_id)
        async with self.db_client() as session:
            try:
                async with session.begin():
                    query = select(Asset).where(
                        Asset.asset_project_id == asset_project_id,
                        Asset.asset_name.ilike(asset_name)  
                    )
                    result = await session.execute(query)
                    asset = result.scalar_one_or_none()
                    if asset:
                        logger.info("Asset found: %s", asset.asset_id)
                    else:
                        logger.warning("No asset found with name '%s' in project_id: %s", asset_name, asset_project_id)
                    return asset
            except SQLAlchemyError as e:
                logger.exception("Error retrieving asset: %s", str(e))
                raise
