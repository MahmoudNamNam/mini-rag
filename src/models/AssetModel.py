import logging
from .BaseDataModel import BaseDataModel
from .db_schemes import Asset
from .enums.DataBaseEnum import DataBaseEnum
from bson import ObjectId, errors as bson_errors

# Configure logger for this module
logger = logging.getLogger(__name__)

class AssetModel(BaseDataModel):

    def __init__(self, db_client: object):
        super().__init__(db_client=db_client)
        self.collection = self.db_client[DataBaseEnum.DATABASE_NAME.value][DataBaseEnum.COLLECTION_ASSET_NAME.value]

    @classmethod
    async def create_instance(cls, db_client: object):
        """
        Factory method to create an instance of AssetModel.
        """
        instance = cls(db_client=db_client)
        await instance.init_collection()
        return instance
    
    async def init_collection(self):
        all_collections = await self.db_client[DataBaseEnum.DATABASE_NAME.value].list_collection_names()
        if DataBaseEnum.COLLECTION_ASSET_NAME.value not in all_collections:
            logger.info("Collection %s does not exist. Creating it now.", DataBaseEnum.COLLECTION_ASSET_NAME.value)
            self.collection = self.db_client[DataBaseEnum.DATABASE_NAME.value][DataBaseEnum.COLLECTION_ASSET_NAME.value]
            indexes = Asset.get_indexes()
            for index in indexes:
                await self.collection.create_index(index["key"], name=index["name"], unique=index.get("unique", False))
            logger.info("Collection %s created and indexes initialized.", DataBaseEnum.COLLECTION_ASSET_NAME.value)

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
    

    async def get_all_project_assets(self, asset_project_id: str):
        logger.info("Fetching all assets for project ID: %s", asset_project_id)
        
        try:
            if isinstance(asset_project_id, str):
                try:
                    asset_project_id = ObjectId(asset_project_id)
                except bson_errors.InvalidId:
                    logger.error("Invalid project ID format: %s", asset_project_id)
                    raise ValueError(f"Invalid project ID format: {asset_project_id}")

            records = await self.collection.find({"project_id": asset_project_id}).to_list(length=None)
            
            if not records:
                logger.warning("No assets found for project ID %s.", asset_project_id)
                return []

            logger.info("Found %d assets for project ID: %s", len(records), asset_project_id)
            return [Asset(**record) for record in records]
        
        except Exception as e:
            logger.exception("Failed to fetch assets for project ID %s: %s (%s)", asset_project_id, str(e), type(e).__name__)
            raise
