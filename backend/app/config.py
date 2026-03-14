"""Application configuration."""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """App settings with defaults."""
    # Sync & Refresh
    refresh_interval_sec: int = 3
    ai_engine_interval_sec: int = 5
    
    # Thresholds
    idle_threshold_sec: int = 30
    focus_sensitivity: str = "medium"  # low, medium, high
    alert_sensitivity: str = "medium"
    
    # App classification (productive apps)
    productive_apps: list[str] = [
        "code", "vscode", "visual studio", "pycharm", "intellij",
        "cursor", "terminal", "cmd", "powershell", "git",
        "notepad", "sublime", "obsidian", "notion"
    ]
    distracting_apps: list[str] = [
        "youtube", "instagram", "facebook", "twitter", "tiktok",
        "netflix", "twitch", "reddit", "games"
    ]
    
    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
