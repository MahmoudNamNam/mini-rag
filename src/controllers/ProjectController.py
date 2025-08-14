from .BaseController import BaseController
import os

class ProjectController(BaseController):
    def __init__(self):
        super().__init__()

    def get_project_path(self, project_id: int) -> str:
        """
        Returns the path to the project directory based on the project ID.
        
        Args:
            project_id (str): The ID of the project.
        
        Returns:
            str: The path to the project directory.
        """
        project_dir = os.path.join(self.files_dir, str(project_id))
        if not os.path.exists(project_dir):
            os.makedirs(project_dir)
        return project_dir