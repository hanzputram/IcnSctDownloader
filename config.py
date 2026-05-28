"""
Configuration loader for IconScout Bot.
Reads from .env file and environment variables.
"""
import os
from pathlib import Path
from dotenv import load_dotenv
from cryptography.fernet import Fernet

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent


class Config:
    # Server
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite+aiosqlite:///{BASE_DIR / 'data' / 'iconscout.db'}")

    # Download settings
    DOWNLOAD_DIR: Path = Path(os.getenv("DOWNLOAD_DIR", str(BASE_DIR / "downloads")))
    DOWNLOAD_DELAY_MIN: int = int(os.getenv("DOWNLOAD_DELAY_MIN", "3"))
    DOWNLOAD_DELAY_MAX: int = int(os.getenv("DOWNLOAD_DELAY_MAX", "6"))
    MAX_CONCURRENT_DOWNLOADS: int = int(os.getenv("MAX_CONCURRENT_DOWNLOADS", "2"))
    DEFAULT_FORMAT: str = os.getenv("DEFAULT_FORMAT", "png")

    # Encryption
    _encryption_key: str = os.getenv("ENCRYPTION_KEY", "")

    @classmethod
    def get_fernet(cls) -> Fernet:
        if not cls._encryption_key:
            # Generate and save a key if not exists
            key = Fernet.generate_key()
            cls._encryption_key = key.decode()
            env_path = BASE_DIR / ".env"
            with open(env_path, "a") as f:
                f.write(f"\nENCRYPTION_KEY={cls._encryption_key}\n")
        return Fernet(cls._encryption_key.encode())

    # Google Drive
    GOOGLE_DRIVE_ENABLED: bool = os.getenv("GOOGLE_DRIVE_ENABLED", "false").lower() == "true"
    GOOGLE_DRIVE_CREDENTIALS_FILE: str = os.getenv("GOOGLE_DRIVE_CREDENTIALS_FILE", "./credentials.json")
    GOOGLE_DRIVE_FOLDER_ID: str = os.getenv("GOOGLE_DRIVE_FOLDER_ID", "")

    # IconScout API (optional)
    ICONSCOUT_API_CLIENT_ID: str = os.getenv("ICONSCOUT_API_CLIENT_ID", "")
    ICONSCOUT_API_CLIENT_SECRET: str = os.getenv("ICONSCOUT_API_CLIENT_SECRET", "")

    # Playwright
    HEADLESS: bool = os.getenv("HEADLESS", "true").lower() == "true"
    BROWSER_TIMEOUT: int = int(os.getenv("BROWSER_TIMEOUT", "30000"))
    
    # Proxy
    _proxy_list_str = os.getenv("PROXY_LIST", "")
    PROXY_LIST: list = [p.strip() for p in _proxy_list_str.split(",")] if _proxy_list_str else []


config = Config()
