from dotenv import load_dotenv
from pathlib import Path
import os
load_dotenv()


class Settings:
    APP_NAME: str = os.getenv(
        "APP_NAME",
        "GitHub Webhook Service",
    )
    
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "sqlite:///./github_app.db",
    )
    
    GITHUB_APP_ID: str = os.getenv(
        "GITHUB_APP_ID",
        "",
    )
    
    GITHUB_PRIVATE_KEY_PATH: str = os.getenv(
        "GITHUB_PRIVATE_KEY_PATH",
        "./github-app-private-key.pem",
    )

    GITHUB_WEBHOOK_SECRET: str = os.getenv(
        "GITHUB_WEBHOOK_SECRET",
        "",
    )

    PUBLIC_BASE_URL: str = os.getenv(
        "PUBLIC_BASE_URL",
        "http://localhost:8000",
    ).rstrip("/")
    
    GITHUB_APP_SLUG : str = os.getenv(
        "GITHUB_APP_SLUG"
    )
    
    
    def github_private_key(self)->str:
        path = Path(self.GITHUB_PRIVATE_KEY_PATH)
        if not path.is_file():
            raise RuntimeError(
                f"GitHub private key not found: {path}"
            )
        return path.read_text(encoding="utf-8")


settings = Settings()
        