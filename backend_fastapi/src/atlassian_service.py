import base64
import httpx
from typing import List, Dict, Any, Optional
from src.models import SessionData, JiraProject, ConfluenceSpace

# PUBLIC_INTERFACE
class AtlassianService:
    """Service for interacting with Atlassian Jira and Confluence APIs."""
    
    # PUBLIC_INTERFACE
    async def get_jira_projects(self, session_data: SessionData) -> List[JiraProject]:
        """
        Fetch Jira projects for the authenticated user.
        
        Args:
            session_data: Session data containing authentication info
            
        Returns:
            List of JiraProject objects
            
        Raises:
            httpx.HTTPError: If API request fails
        """
        # Prepare authentication header
        auth_header = self._get_auth_header(session_data)
        
        # Make API request
        url = f"https://{session_data.domain}/rest/api/3/project"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers={'Authorization': auth_header},
                timeout=30.0
            )
            
            response.raise_for_status()
            projects_data = response.json()
            
            # Convert to Pydantic models
            projects = []
            for project_data in projects_data:
                project = JiraProject(
                    id=project_data['id'],
                    key=project_data['key'],
                    name=project_data['name'],
                    project_type_key=project_data['projectTypeKey'],
                    simplified=project_data.get('simplified', False),
                    style=project_data.get('style', 'classic'),
                    is_private=project_data.get('isPrivate', False),
                    avatar_urls=project_data.get('avatarUrls', {})
                )
                projects.append(project)
            
            return projects
    
    # PUBLIC_INTERFACE
    async def get_confluence_spaces(self, session_data: SessionData) -> List[ConfluenceSpace]:
        """
        Fetch Confluence spaces for the authenticated user.
        
        Args:
            session_data: Session data containing authentication info
            
        Returns:
            List of ConfluenceSpace objects
            
        Raises:
            httpx.HTTPError: If API request fails
        """
        # Prepare authentication header
        auth_header = self._get_auth_header(session_data)
        
        # Make API request
        url = f"https://{session_data.domain}/wiki/rest/api/space"
        params = {'expand': 'homepage', 'limit': 100}
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers={'Authorization': auth_header},
                params=params,
                timeout=30.0
            )
            
            response.raise_for_status()
            response_data = response.json()
            spaces_data = response_data.get('results', [])
            
            # Convert to Pydantic models
            spaces = []
            for space_data in spaces_data:
                space = ConfluenceSpace(
                    id=space_data['id'],
                    key=space_data['key'],
                    name=space_data['name'],
                    type=space_data['type'],
                    status=space_data['status'],
                    homepage=space_data.get('homepage')
                )
                spaces.append(space)
            
            return spaces
    
    # PUBLIC_INTERFACE
    async def test_connection(self, session_data: SessionData) -> Dict[str, Any]:
        """
        Test the connection to Atlassian services.
        
        Args:
            session_data: Session data containing authentication info
            
        Returns:
            Dict containing connection test results
            
        Raises:
            httpx.HTTPError: If connection test fails
        """
        auth_header = self._get_auth_header(session_data)
        
        if session_data.service == 'jira':
            test_url = f"https://{session_data.domain}/rest/api/3/myself"
        else:  # confluence
            test_url = f"https://{session_data.domain}/wiki/rest/api/user/current"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                test_url,
                headers={'Authorization': auth_header},
                timeout=10.0
            )
            
            response.raise_for_status()
            user_data = response.json()
            
            return {
                'status': 'connected',
                'service': session_data.service,
                'domain': session_data.domain,
                'user': user_data,
                'auth_type': session_data.auth_type
            }
    
    def _get_auth_header(self, session_data: SessionData) -> str:
        """Generate appropriate authorization header based on auth type."""
        if session_data.auth_type == 'oauth':
            return f"Bearer {session_data.access_token}"
        elif session_data.token_type == 'Basic':
            # For API tokens with email (already base64 encoded in access_token)
            return f"Basic {session_data.access_token}"
        else:
            # For Personal Access Tokens
            return f"Bearer {session_data.access_token}"

# Global Atlassian service instance
atlassian_service = AtlassianService()
