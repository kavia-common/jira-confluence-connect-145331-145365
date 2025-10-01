from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

# PUBLIC_INTERFACE
class OAuthStartResponse(BaseModel):
    """Response model for OAuth start endpoint."""
    authorization_url: str = Field(..., description="OAuth authorization URL to redirect user to")
    state: str = Field(..., description="OAuth state parameter for security")

# PUBLIC_INTERFACE
class OAuthCallbackRequest(BaseModel):
    """Request model for OAuth callback endpoint."""
    code: str = Field(..., description="OAuth authorization code")
    state: str = Field(..., description="OAuth state parameter")

# PUBLIC_INTERFACE
class APITokenRequest(BaseModel):
    """Request model for API token authentication."""
    api_token: str = Field(..., description="API token or Personal Access Token")
    email: Optional[str] = Field(None, description="Email address (required for Jira API tokens)")
    domain: str = Field(..., description="Atlassian domain (e.g., yourcompany.atlassian.net)")

# PUBLIC_INTERFACE
class AuthenticationResponse(BaseModel):
    """Response model for successful authentication."""
    session_token: str = Field(..., description="Session token for authenticated requests")
    user_info: Dict[str, Any] = Field(..., description="User information from Atlassian")
    expires_in: int = Field(..., description="Token expiration time in seconds")

# PUBLIC_INTERFACE
class JiraProject(BaseModel):
    """Model for Jira project information."""
    id: str = Field(..., description="Project ID")
    key: str = Field(..., description="Project key")
    name: str = Field(..., description="Project name")
    project_type_key: str = Field(..., description="Project type")
    simplified: bool = Field(..., description="Is simplified project")
    style: str = Field(..., description="Project style")
    is_private: bool = Field(..., description="Is private project")
    avatar_urls: Dict[str, str] = Field(..., description="Avatar URLs")

# PUBLIC_INTERFACE
class ConfluenceSpace(BaseModel):
    """Model for Confluence space information."""
    id: str = Field(..., description="Space ID")
    key: str = Field(..., description="Space key")
    name: str = Field(..., description="Space name")
    type: str = Field(..., description="Space type")
    status: str = Field(..., description="Space status")
    homepage: Optional[Dict[str, Any]] = Field(None, description="Homepage information")

# PUBLIC_INTERFACE
class ProjectsResponse(BaseModel):
    """Response model for Jira projects list."""
    projects: List[JiraProject] = Field(..., description="List of Jira projects")
    total: int = Field(..., description="Total number of projects")

# PUBLIC_INTERFACE
class SpacesResponse(BaseModel):
    """Response model for Confluence spaces list."""
    spaces: List[ConfluenceSpace] = Field(..., description="List of Confluence spaces")
    total: int = Field(..., description="Total number of spaces")

# PUBLIC_INTERFACE
class ErrorResponse(BaseModel):
    """Response model for error responses."""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")

# Internal models for session management
class SessionData(BaseModel):
    """Internal model for session data storage."""
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "Bearer"
    expires_at: datetime
    user_info: Dict[str, Any]
    service: str  # 'jira' or 'confluence'
    domain: str
    auth_type: str  # 'oauth' or 'api_token'
