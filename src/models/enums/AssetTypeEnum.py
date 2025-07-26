from enum import Enum

class AssetTypeEnum(str, Enum):
    """
    Enum for different types of assets.
    """
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    DOCUMENT = "document"
    OTHER = "other"
