import secrets
import base64
import httpx
from datetime import datetime, timedelta
from typing import Dict, Any, Tuple, Optional
from urllib.parse import urlencode

from src.config import config
from src.models import SessionData

# PUBLIC_INTERFACE
class AuthService:
    """Service for handling Atlassian OAuth and API token authentication."""
    
    def __init__(self):
        self.oauth_states: Dict[str, str] = {}  # state -> service mapping
    
    # PUBLIC_INTERFACE
    async def start_oauth_flow(self, service: str) -> Tuple[str, str]:
        """
        Start OAuth flow for Jira or Confluence.
        
        Args:
            service: 'jira' or 'confluence'
            
        Returns:
            Tuple of (authorization_url, state)
        """
        # Generate secure state parameter
        state = secrets.token_urlsafe(32)
        self.oauth_states[state] = service
        
        # OAuth scopes for different services
        scopes = {
            'jira': 'read:jira-user read:jira-work offline_access',
            'confluence': 'read:confluence-user read:confluence-content.summary offline_access'
        }
        
        # Build authorization URL
        auth_params = {
            'audience': 'api.atlassian.com',
            'client_id': config.ATLASSIAN_CLIENT_ID,
            'scope': scopes.get(service, 'offline_access'),
            'redirect_uri': f"{config.REDIRECT_URI}/auth/{service}/oauth/callback",
            'state': state,
            'response_type': 'code',
            'prompt': 'consent'
        }
        
        authorization_url = f"{config.ATLASSIAN_AUTH_URL}?{urlencode(auth_params)}"
        
        return authorization_url, state
    
    # PUBLIC_INTERFACE
    async def handle_oauth_callback(self, code: str, state: str) -> SessionData:
        """
        Handle OAuth callback and exchange code for tokens.
        
        Args:
            code: Authorization code from callback
            state: State parameter from callback
            
        Returns:
            SessionData: Created session data
            
        Raises:
            ValueError: If state is invalid or token exchange fails
        """
        # Validate state
        if state not in self.oauth_states:
            raise ValueError("Invalid or expired state parameter")
        
        service = self.oauth_states[state]
        del self.oauth_states[state]  # Remove used state
        
        # Exchange code for tokens
        token_data = await self._exchange_code_for_tokens(code, service)
        
        # Get user info and accessible resources
        user_info = await self._get_user_info(token_data['access_token'])
        accessible_resources = await self._get_accessible_resources(token_data['access_token'])
        
        # Select the first available resource (domain)
        if not accessible_resources:
            raise ValueError("No accessible Atlassian resources found")
        
        domain = accessible_resources[0]['url'].replace('https://', '').replace('http://', '')
        
        # Create session data
        expires_at = datetime.utcnow() + timedelta(seconds=token_data.get('expires_in', 3600))
        
        session_data = SessionData(
            access_token=token_data['access_token'],
            refresh_token=token_data.get('refresh_token'),
            token_type=token_data.get('token_type', 'Bearer'),
            expires_at=expires_at,
            user_info=user_info,
            service=service,
            domain=domain,
            auth_type='oauth'
        )
        
        return session_data
    
    # PUBLIC_INTERFACE
    async def authenticate_with_api_token(self, api_token: str, email: Optional[str], domain: str, service: str) -> SessionData:
        """
        Authenticate using API token or Personal Access Token.
        
        Args:
            api_token: API token or PAT
            email: Email address (required for Jira API tokens)
            domain: Atlassian domain
            service: 'jira' or 'confluence'
            
        Returns:
            SessionData: Created session data
            
        Raises:
            ValueError: If authentication fails
        """
        # Test the token by making a test API call
        user_info = await self._test_api_token(api_token, email, domain, service)
        
        # Create session data - API tokens don't expire but we set a reasonable session expiry
        expires_at = datetime.utcnow() + timedelta(hours=config.SESSION_EXPIRY_HOURS)
        
        session_data = SessionData(
            access_token=api_token,
            refresh_token=None,
            token_type='Basic' if email else 'Bearer',
            expires_at=expires_at,
            user_info=user_info,
            service=service,
            domain=domain,
            auth_type='api_token'
        )
        
        return session_data
    
    async def _exchange_code_for_tokens(self, code: str, service: str) -> Dict[str, Any]:
        """Exchange authorization code for access tokens."""
        # Prepare token request
        token_data = {
            'grant_type': 'authorization_code',
            'client_id': config.ATLASSIAN_CLIENT_ID,
            'client_secret': config.ATLASSIAN_CLIENT_SECRET,
            'code': code,
            'redirect_uri': f"{config.REDIRECT_URI}/auth/{service}/oauth/callback"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                config.ATLASSIAN_TOKEN_URL,
                data=token_data,
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )
            
            if response.status_code != 200:
                raise ValueError(f"Token exchange failed: {response.text}")
            
            return response.json()
    
    async def _get_user_info(self, access_token: str) -> Dict[str, Any]:
        """Get user information using access token."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.atlassian.com/me",
                headers={'Authorization': f'Bearer {access_token}'}
            )
            
            if response.status_code != 200:
                raise ValueError(f"Failed to get user info: {response.text}")
            
            return response.json()
    
    async def _get_accessible_resources(self, access_token: str) -> list:
        """Get accessible Atlassian resources."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                config.ATLASSIAN_ACCESSIBLE_RESOURCES_URL,
                headers={'Authorization': f'Bearer {access_token}'}
            )
            
            if response.status_code != 200:
                raise ValueError(f"Failed to get accessible resources: {response.text}")
            
            return response.json()
    
    async def _test_api_token(self, api_token: str, email: Optional[str], domain: str, service: str) -> Dict[str, Any]:
        """Test API token by making a test API call."""
        # Prepare authentication header
        if email:
            # Basic auth for Jira API tokens
            credentials = base64.b64encode(f"{email}:{api_token}".encode()).decode()
            auth_header = f"Basic {credentials}"
        else:
            # Bearer token for PATs
            auth_header = f"Bearer {api_token}"
        
        # Test endpoint based on service
        if service == 'jira':
            test_url = f"https://{domain}/rest/api/3/myself"
        else:  # confluence
            test_url = f"https://{domain}/wiki/rest/api/user/current"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                test_url,
                headers={'Authorization': auth_header}
            )
            
            if response.status_code != 200:
                raise ValueError(f"API token authentication failed: {response.text}")
            
            return response.json()

# Global auth service instance
auth_service = AuthService()
