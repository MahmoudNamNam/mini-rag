from helper.config import get_settings, Settings

class BaseDataModel:
    """
    Base data model class for handling common functionality across data models.
    """
    def __init__(self, db_client: object):
        self.db_client = db_client
        self.settings = get_settings()

