import logging
import re
from .BaseDataModel import BaseDataModel
from .db_schemes import Asset
from .enums.DataBaseEnum import DataBaseEnum
from bson import ObjectId, errors as bson_errors
from pydantic import ValidationError


# Configure logger for this module
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
        self.collection = self.get_collection(DataBaseEnum.COLLECTION_ASSET_NAME.value)


    @classmethod
    async def create_instance(cls, db_client: object):
        """
        Factory method to create an instance of AssetModel.
        """
        instance = cls(db_client=db_client)
        await instance.init_collection()
        return instance
    
    async def init_collection(self):
        indexes = Asset.get_indexes()
        await self.init_collection_with_indexes(
            DataBaseEnum.COLLECTION_ASSET_NAME.value,
            indexes
        )

    async def create_asset(self, asset: Asset):
        logger.info("Attempting to create asset with ID: %s", asset.id)
        try:
            result = await self.collection.insert_one(asset.dict(by_alias=True, exclude_unset=True))
            asset.id = result.inserted_id
            logger.info("Asset created successfully with ObjectId: %s", result.inserted_id)
            return asset
        except Exception as e:
            logger.exception("Failed to create asset with ID %s: %s", asset.id, str(e))
            raise
    


    async def get_all_project_assets(self, asset_project_id: str, asset_type: str):
        logger.info("Fetching all assets for project_id: %s with type: %s", asset_project_id, asset_type)

        try:
            query = {
                "asset_project_id": ObjectId(asset_project_id) if isinstance(asset_project_id, str) else asset_project_id,
                "asset_type": asset_type,
            }

            records = await self.collection.find(query).to_list(length=None)
            logger.info("Found %d assets for project_id: %s", len(records), asset_project_id)

            return [Asset(**record) for record in records]

        except bson_errors.InvalidId:
            logger.error("Invalid ObjectId provided for asset_project_id: %s", asset_project_id)
            raise
        except Exception as e:
            logger.exception("Unexpected error while retrieving assets for project_id %s: %s", asset_project_id, str(e))
            raise

    async def get_asset_record(self, asset_project_id: str, asset_name: str):
        logger.info("Looking up asset with name '%s' in project_id: %s", asset_name, asset_project_id)

        try:
            query = {
                "asset_project_id": ObjectId(asset_project_id) if isinstance(asset_project_id, str) else asset_project_id,
                "asset_name": {"$regex": f"^{re.escape(asset_name)}$", "$options": "i"}
            }

            record = await self.collection.find_one(query)

            if record:
                logger.info("Asset found: %s", record.get("_id"))
                return Asset(**record)
            else:
                logger.warning("No asset found with name '%s' in project_id: %s", asset_name, asset_project_id)
                return None

        except bson_errors.InvalidId:
            logger.error("Invalid ObjectId provided for asset_project_id: %s", asset_project_id)
            raise
        except Exception as e:
            logger.exception("Error retrieving asset '%s' from project_id %s: %s", asset_name, asset_project_id, str(e))
            raise