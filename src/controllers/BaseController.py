from helper.config import get_settings, Settings
from pathlib import Path
import os

class BaseController:
    """
    Base controller class for handling common functionality across controllers.
    """
    def __init__(self):
        self.app_settings = get_settings()
        self.base_path = Path(__file__).resolve().parents[1]
        self.files_dir = self.base_path / "assets" / "files"

    def get_app_settings(self):
        """
        Returns the application settings.
        """
        return self.app_settings

    def handle_error(self, error):
        """
        Handles errors and returns a standardized error response.
        """
        return {"error": str(error)}