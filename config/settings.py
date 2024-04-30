from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
from os import path

ENV_PATH = path.join(Path(__file__).parent, ".env")
class Settings(BaseSettings):
        mongodb_uri: str
        mongodb_atlas_uri: str
        algorithm: str
        access_token_secret_key: str
        access_token_secret_key_expiry: str
        refresh_token_secret_key: str
        refresh_token_secret_key_expiry: str
        environment: str 
        api_version: int | str
        db_name: str
        smtp_host: str
        smtp_port: int
        smtp_pass: str
        smtp_user: str
        temp_token_expiry: int
        temp_token_secret: str 
        google_client_id: str
        google_client_secret: str
        session_secret: str
        model_config =  SettingsConfigDict(env_file = ENV_PATH)


def get_setting():
    settings = Settings()
    while True:
        yield settings


setting_gena = get_setting()
setting = next(setting_gena)

def settings() -> Settings:
     return setting

__all__ = ("settings")