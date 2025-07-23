from helper.config import get_settings, Settings
from pathlib import Path
import random
import string


class BaseController:
    """
    Base controller class for handling common functionality across controllers.
    """
    def __init__(self):
        self.app_settings = get_settings()
        self.base_path = Path(__file__).resolve().parents[1]
        self.files_dir = self.base_path / "assets" / "files"
        self.files_dir.mkdir(parents=True, exist_ok=True)  

    def generate_unique_key(self, length: int = 12) -> str:

        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

    def get_app_settings(self):
        """
        Returns the application settings.
        """
        return self.app_settings