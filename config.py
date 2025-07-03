"""
Configuration management for the bot
"""
import os
from typing import List, Optional

class Config:
    """Bot configuration class"""
    
    # Required environment variables
    API_ID: int = int(os.environ.get("API_ID", 0))
    API_HASH: str = os.environ.get("API_HASH", "")
    BOT_TOKEN: str = os.environ.get("BOT_TOKEN", "")
    
    # Optional environment variables
    ADMIN_IDS: List[int] = [
        int(x.strip()) for x in os.environ.get("ADMIN_IDS", "").split(",") 
        if x.strip().isdigit()
    ]
    
    MAX_FILE_SIZE: int = int(os.environ.get("MAX_FILE_SIZE", "2147483648"))  # 2GB
    WATERMARK_TEXT: str = os.environ.get("WATERMARK_TEXT", "@YourBrand")
    
    # Processing settings
    MAX_CONCURRENT_PROCESSES: int = int(os.environ.get("MAX_CONCURRENT_PROCESSES", "3"))
    SESSION_TIMEOUT: int = int(os.environ.get("SESSION_TIMEOUT", "3600"))  # 1 hour
    
    # Quality settings
    DEFAULT_QUALITY: str = os.environ.get("DEFAULT_QUALITY", "fast")
    DEFAULT_RESOLUTION: str = os.environ.get("DEFAULT_RESOLUTION", "720p")
    DEFAULT_FORMAT: str = os.environ.get("DEFAULT_FORMAT", "mp4")
    
    # Directories
    DOWNLOAD_DIR: str = "downloads"
    OUTPUT_DIR: str = "outputs"
    TEMP_DIR: str = "temp"
    LOG_DIR: str = "logs"
    
    @classmethod
    def validate(cls) -> bool:
        """Validate required configuration"""
        required_vars = ["API_ID", "API_HASH", "BOT_TOKEN"]
        missing_vars = []
        
        for var in required_vars:
            if not getattr(cls, var):
                missing_vars.append(var)
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        return True
    
    @classmethod
    def create_directories(cls) -> None:
        """Create necessary directories"""
        directories = [cls.DOWNLOAD_DIR, cls.OUTPUT_DIR, cls.TEMP_DIR, cls.LOG_DIR]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)