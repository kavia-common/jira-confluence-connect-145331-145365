import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# PUBLIC_INTERFACE
class Config:
    """Configuration class for FastAPI application."""
    
    # Atlassian OAuth credentials
    ATLASSIAN_CLIENT_ID: str = os.getenv("ATLASSIAN_CLIENT_ID", "")
    ATLASSIAN_CLIENT_SECRET: str = os.getenv("ATLASSIAN_CLIENT_SECRET", "")
    REDIRECT_URI: str = os.getenv("REDIRECT_URI", "http://localhost:3001")
    
    # OAuth endpoints
    ATLASSIAN_AUTH_URL: str = "https://auth.atlassian.com/authorize"
    ATLASSIAN_TOKEN_URL: str = "https://auth.atlassian.com/oauth/token"
    ATLASSIAN_ACCESSIBLE_RESOURCES_URL: str = "https://api.atlassian.com/oauth/token/accessible-resources"
    
    # Session configuration
    SESSION_EXPIRY_HOURS: int = 24
    
    # CORS configuration
    CORS_ORIGINS: list = ["http://localhost:3000", "https://localhost:3000"]
    
    @classmethod
    def validate_config(cls) -> bool:
        """Validate that required configuration is present."""
        required_vars = [
            "ATLASSIAN_CLIENT_ID",
            "ATLASSIAN_CLIENT_SECRET", 
            "REDIRECT_URI"
        ]
        
        missing_vars = []
        for var in required_vars:
            if not getattr(cls, var):
                missing_vars.append(var)
        
        if missing_vars:
            print(f"Warning: Missing required environment variables: {', '.join(missing_vars)}")
            return False
        
        return True

# Create global config instance
config = Config()
