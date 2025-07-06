from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Configuration settings for the application.
    """
    APP_NAME: str 
    APP_VERSION: str
    APP_DESCRIPTION: str

    class Config:
        """
        Configuration for Pydantic settings.
        """
        env_file = ".env"


def get_settings() -> Settings:
    """
    Retrieve the application settings.

    Returns:
        Settings: An instance of the Settings class containing configuration values.
    """
    return Settings()