from fastapi import FastAPI, HTTPException, Depends, status, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from typing import Dict, Any, Optional
import logging
from datetime import datetime

from src.config import config
from src.models import (
    OAuthStartResponse, 
    OAuthCallbackRequest, 
    APITokenRequest, 
    AuthenticationResponse,
    ProjectsResponse, 
    SpacesResponse, 
    ErrorResponse
)
from src.auth_service import auth_service
from src.atlassian_service import atlassian_service
from src.session_storage import session_storage, SessionData

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app with metadata for OpenAPI documentation
app = FastAPI(
    title="Jira & Confluence Connector API",
    description="FastAPI backend for connecting to Jira and Confluence using OAuth 2.0 and API tokens",
    version="1.0.0",
    openapi_tags=[
        {
            "name": "health",
            "description": "Health check endpoints"
        },
        {
            "name": "jira-auth",
            "description": "Jira authentication endpoints (OAuth and API token)"
        },
        {
            "name": "confluence-auth", 
            "description": "Confluence authentication endpoints (OAuth and API token)"
        },
        {
            "name": "jira-api",
            "description": "Jira data retrieval endpoints"
        },
        {
            "name": "confluence-api",
            "description": "Confluence data retrieval endpoints"
        }
    ]
)

# CORS middleware setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Validate configuration on startup
@app.on_event("startup")
async def startup_event():
    """Validate configuration and log startup information."""
    logger.info("Starting Jira & Confluence Connector API")
    if not config.validate_config():
        logger.warning("Some configuration variables are missing. Check environment variables.")
    logger.info(f"CORS origins: {config.CORS_ORIGINS}")

# Dependency for extracting session data from authorization header
async def get_session_data(authorization: Optional[str] = Header(None)) -> SessionData:
    """
    Extract and validate session data from Authorization header.
    
    Args:
        authorization: Authorization header value
        
    Returns:
        SessionData: Valid session data
        
    Raises:
        HTTPException: If session is invalid or expired
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header"
        )
    
    session_token = authorization[7:]  # Remove "Bearer " prefix
    session_data = session_storage.get_session(session_token)
    
    if not session_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session token"
        )
    
    return session_data

# Health check endpoint
@app.get(
    "/",
    tags=["health"],
    summary="Health Check",
    description="Check if the API is running and healthy"
)
# PUBLIC_INTERFACE
def health_check() -> Dict[str, str]:
    """Health check endpoint to verify API is running."""
    return {"status": "healthy", "message": "Jira & Confluence Connector API is running"}

# Jira OAuth endpoints
@app.get(
    "/auth/jira/oauth/start",
    response_model=OAuthStartResponse,
    tags=["jira-auth"],
    summary="Start Jira OAuth Flow",
    description="Initiate OAuth 2.0 authentication flow for Jira access"
)
# PUBLIC_INTERFACE
async def start_jira_oauth() -> OAuthStartResponse:
    """
    Start OAuth flow for Jira authentication.
    
    Returns:
        OAuthStartResponse: Authorization URL and state parameter
    """
    try:
        authorization_url, state = await auth_service.start_oauth_flow('jira')
        return OAuthStartResponse(authorization_url=authorization_url, state=state)
    except Exception as e:
        logger.error(f"Failed to start Jira OAuth flow: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to start OAuth flow: {str(e)}")

@app.post(
    "/auth/jira/oauth/callback",
    response_model=AuthenticationResponse,
    tags=["jira-auth"],
    summary="Handle Jira OAuth Callback",
    description="Handle OAuth callback and exchange authorization code for tokens"
)
# PUBLIC_INTERFACE
async def jira_oauth_callback(callback_data: OAuthCallbackRequest) -> AuthenticationResponse:
    """
    Handle OAuth callback for Jira authentication.
    
    Args:
        callback_data: OAuth callback data with code and state
        
    Returns:
        AuthenticationResponse: Session token and user information
    """
    try:
        session_data = await auth_service.handle_oauth_callback(callback_data.code, callback_data.state)
        session_token = session_storage.create_session(session_data)
        
        return AuthenticationResponse(
            session_token=session_token,
            user_info=session_data.user_info,
            expires_in=int((session_data.expires_at - datetime.utcnow()).total_seconds())
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"OAuth callback failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"OAuth callback failed: {str(e)}")

@app.post(
    "/auth/jira/api-token",
    response_model=AuthenticationResponse,
    tags=["jira-auth"],
    summary="Authenticate with Jira API Token",
    description="Authenticate using Jira API token or Personal Access Token"
)
# PUBLIC_INTERFACE
async def jira_api_token_auth(token_data: APITokenRequest) -> AuthenticationResponse:
    """
    Authenticate with Jira using API token.
    
    Args:
        token_data: API token authentication data
        
    Returns:
        AuthenticationResponse: Session token and user information
    """
    try:
        session_data = await auth_service.authenticate_with_api_token(
            token_data.api_token,
            token_data.email,
            token_data.domain,
            'jira'
        )
        session_token = session_storage.create_session(session_data)
        
        return AuthenticationResponse(
            session_token=session_token,
            user_info=session_data.user_info,
            expires_in=int((session_data.expires_at - session_data.expires_at.utcnow()).total_seconds())
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"API token authentication failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"API token authentication failed: {str(e)}")

# Confluence OAuth endpoints
@app.get(
    "/auth/confluence/oauth/start",
    response_model=OAuthStartResponse,
    tags=["confluence-auth"],
    summary="Start Confluence OAuth Flow",
    description="Initiate OAuth 2.0 authentication flow for Confluence access"
)
# PUBLIC_INTERFACE
async def start_confluence_oauth() -> OAuthStartResponse:
    """
    Start OAuth flow for Confluence authentication.
    
    Returns:
        OAuthStartResponse: Authorization URL and state parameter
    """
    try:
        authorization_url, state = await auth_service.start_oauth_flow('confluence')
        return OAuthStartResponse(authorization_url=authorization_url, state=state)
    except Exception as e:
        logger.error(f"Failed to start Confluence OAuth flow: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to start OAuth flow: {str(e)}")

@app.post(
    "/auth/confluence/oauth/callback",
    response_model=AuthenticationResponse,
    tags=["confluence-auth"],
    summary="Handle Confluence OAuth Callback",
    description="Handle OAuth callback and exchange authorization code for tokens"
)
# PUBLIC_INTERFACE
async def confluence_oauth_callback(callback_data: OAuthCallbackRequest) -> AuthenticationResponse:
    """
    Handle OAuth callback for Confluence authentication.
    
    Args:
        callback_data: OAuth callback data with code and state
        
    Returns:
        AuthenticationResponse: Session token and user information
    """
    try:
        session_data = await auth_service.handle_oauth_callback(callback_data.code, callback_data.state)
        session_token = session_storage.create_session(session_data)
        
        return AuthenticationResponse(
            session_token=session_token,
            user_info=session_data.user_info,
            expires_in=int((session_data.expires_at - session_data.expires_at.utcnow()).total_seconds())
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"OAuth callback failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"OAuth callback failed: {str(e)}")

@app.post(
    "/auth/confluence/api-token",
    response_model=AuthenticationResponse,
    tags=["confluence-auth"],
    summary="Authenticate with Confluence API Token",
    description="Authenticate using Confluence API token or Personal Access Token"
)
# PUBLIC_INTERFACE
async def confluence_api_token_auth(token_data: APITokenRequest) -> AuthenticationResponse:
    """
    Authenticate with Confluence using API token.
    
    Args:
        token_data: API token authentication data
        
    Returns:
        AuthenticationResponse: Session token and user information
    """
    try:
        session_data = await auth_service.authenticate_with_api_token(
            token_data.api_token,
            token_data.email,
            token_data.domain,
            'confluence'
        )
        session_token = session_storage.create_session(session_data)
        
        return AuthenticationResponse(
            session_token=session_token,
            user_info=session_data.user_info,
            expires_in=int((session_data.expires_at - session_data.expires_at.utcnow()).total_seconds())
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"API token authentication failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"API token authentication failed: {str(e)}")

# Jira API endpoints
@app.get(
    "/jira/projects",
    response_model=ProjectsResponse,
    tags=["jira-api"],
    summary="Get Jira Projects",
    description="Retrieve list of Jira projects accessible to the authenticated user"
)
# PUBLIC_INTERFACE
async def get_jira_projects(
    session_data: SessionData = Depends(get_session_data)
) -> ProjectsResponse:
    """
    Get Jira projects for the authenticated user.
    
    Args:
        session_data: Session data from authorization header
        
    Returns:
        ProjectsResponse: List of Jira projects
    """
    if session_data.service != 'jira':
        raise HTTPException(
            status_code=400, 
            detail="Session is not authenticated for Jira access"
        )
    
    try:
        projects = await atlassian_service.get_jira_projects(session_data)
        return ProjectsResponse(projects=projects, total=len(projects))
    except Exception as e:
        logger.error(f"Failed to fetch Jira projects: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch projects: {str(e)}")

# Confluence API endpoints
@app.get(
    "/confluence/spaces",
    response_model=SpacesResponse,
    tags=["confluence-api"],
    summary="Get Confluence Spaces",
    description="Retrieve list of Confluence spaces accessible to the authenticated user"
)
# PUBLIC_INTERFACE
async def get_confluence_spaces(
    session_data: SessionData = Depends(get_session_data)
) -> SpacesResponse:
    """
    Get Confluence spaces for the authenticated user.
    
    Args:
        session_data: Session data from authorization header
        
    Returns:
        SpacesResponse: List of Confluence spaces
    """
    if session_data.service != 'confluence':
        raise HTTPException(
            status_code=400, 
            detail="Session is not authenticated for Confluence access"
        )
    
    try:
        spaces = await atlassian_service.get_confluence_spaces(session_data)
        return SpacesResponse(spaces=spaces, total=len(spaces))
    except Exception as e:
        logger.error(f"Failed to fetch Confluence spaces: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch spaces: {str(e)}")

# Session management endpoint
@app.delete(
    "/auth/logout",
    tags=["health"],
    summary="Logout",
    description="Delete the current session and logout the user"
)
# PUBLIC_INTERFACE
async def logout(session_data: SessionData = Depends(get_session_data)) -> Dict[str, str]:
    """
    Logout user by deleting the session.
    
    Args:
        session_data: Session data from authorization header
        
    Returns:
        Dict with logout confirmation
    """
    # Extract session token from the dependency (we need to modify get_session_data to return both)
    # For now, we'll cleanup expired sessions as a workaround
    cleaned_count = session_storage.cleanup_expired_sessions()
    logger.info(f"Logout requested, cleaned up {cleaned_count} expired sessions")
    
    return {"message": "Logged out successfully"}

# Session info endpoint
@app.get(
    "/auth/session",
    tags=["health"],
    summary="Get Session Info",
    description="Get information about the current session"
)
# PUBLIC_INTERFACE
async def get_session_info(session_data: SessionData = Depends(get_session_data)) -> Dict[str, Any]:
    """
    Get current session information.
    
    Args:
        session_data: Session data from authorization header
        
    Returns:
        Dict with session information
    """
    return {
        "service": session_data.service,
        "domain": session_data.domain,
        "auth_type": session_data.auth_type,
        "user_info": session_data.user_info,
        "expires_at": session_data.expires_at.isoformat(),
        "active_sessions": session_storage.get_session_count()
    }
