# Jira & Confluence Connector - FastAPI Backend

A FastAPI backend for connecting to Jira and Confluence using OAuth 2.0 and API tokens. This service provides authentication flows and data retrieval endpoints for both Jira and Confluence.

## Features

- **OAuth 2.0 Authentication**: Secure authentication flow for Jira and Confluence
- **API Token Support**: Alternative authentication using API tokens or Personal Access Tokens
- **In-Memory Session Storage**: Session management without database dependencies
- **Comprehensive API**: Well-documented endpoints with Swagger/OpenAPI
- **Error Handling**: Robust error handling with detailed responses
- **CORS Support**: Configured for frontend integration

## Project Structure

```
backend_fastapi/
├── src/
│   ├── api/
│   │   ├── main.py              # FastAPI application and route definitions
│   │   ├── generate_openapi.py  # OpenAPI schema generation
│   │   └── __init__.py
│   ├── models.py                # Pydantic models for request/response
│   ├── config.py                # Configuration management
│   ├── session_storage.py       # In-memory session storage
│   ├── auth_service.py          # Authentication service (OAuth & API tokens)
│   └── atlassian_service.py     # Atlassian API integration
├── interfaces/
│   └── openapi.json            # Generated OpenAPI specification
├── requirements.txt            # Python dependencies
├── .env.example               # Environment variables template
└── README.md                  # This file
```

## API Endpoints

### Health Check
- `GET /` - Health check endpoint

### Jira Authentication
- `GET /auth/jira/oauth/start` - Start Jira OAuth flow
- `POST /auth/jira/oauth/callback` - Handle OAuth callback
- `POST /auth/jira/api-token` - Authenticate with API token

### Confluence Authentication
- `GET /auth/confluence/oauth/start` - Start Confluence OAuth flow
- `POST /auth/confluence/oauth/callback` - Handle OAuth callback
- `POST /auth/confluence/api-token` - Authenticate with API token

### Data Retrieval
- `GET /jira/projects` - Get Jira projects (requires authentication)
- `GET /confluence/spaces` - Get Confluence spaces (requires authentication)

### Session Management
- `GET /auth/session` - Get current session info
- `DELETE /auth/logout` - Logout and delete session

## Setup and Installation

### 1. Environment Setup

Copy the environment template and configure your Atlassian app credentials:

```bash
cp .env.example .env
```

Edit `.env` with your Atlassian Developer Console app details:

```env
ATLASSIAN_CLIENT_ID=your_atlassian_client_id_here
ATLASSIAN_CLIENT_SECRET=your_atlassian_client_secret_here
REDIRECT_URI=http://localhost:3001
```

### 2. Install Dependencies

Create a virtual environment and install dependencies:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Run the Application

Start the FastAPI development server:

```bash
uvicorn src.api.main:app --host 0.0.0.0 --port 3001 --reload
```

The API will be available at:
- **API Base URL**: http://localhost:3001
- **Interactive Documentation**: http://localhost:3001/docs
- **OpenAPI Schema**: http://localhost:3001/openapi.json

## Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `ATLASSIAN_CLIENT_ID` | Atlassian OAuth app client ID | Yes | - |
| `ATLASSIAN_CLIENT_SECRET` | Atlassian OAuth app client secret | Yes | - |
| `REDIRECT_URI` | OAuth redirect URI | Yes | http://localhost:3001 |

### Atlassian Developer Setup

1. Go to [Atlassian Developer Console](https://developer.atlassian.com/console)
2. Create a new OAuth 2.0 (3LO) app
3. Configure OAuth 2.0 settings:
   - **Authorization callback URL**: `http://localhost:3001/auth/jira/oauth/callback` and `http://localhost:3001/auth/confluence/oauth/callback`
   - **Scopes**: 
     - Jira: `read:jira-user`, `read:jira-work`, `offline_access`
     - Confluence: `read:confluence-user`, `read:confluence-content.summary`, `offline_access`

## Authentication Flows

### OAuth 2.0 Flow

1. **Start OAuth**: Call `/auth/{service}/oauth/start` to get authorization URL
2. **User Authorization**: Redirect user to authorization URL
3. **Handle Callback**: Process callback at `/auth/{service}/oauth/callback`
4. **Use Session Token**: Include `Authorization: Bearer <session_token>` in API requests

### API Token Flow

1. **Authenticate**: POST to `/auth/{service}/api-token` with credentials
2. **Get Session Token**: Receive session token in response
3. **Use Session Token**: Include `Authorization: Bearer <session_token>` in API requests

## Usage Examples

### Start OAuth Flow (JavaScript)

```javascript
// Start Jira OAuth
const response = await fetch('http://localhost:3001/auth/jira/oauth/start');
const { authorization_url, state } = await response.json();

// Redirect user to authorization URL
window.location.href = authorization_url;
```

### API Token Authentication (JavaScript)

```javascript
// Authenticate with API token
const response = await fetch('http://localhost:3001/auth/jira/api-token', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    api_token: 'your_api_token',
    email: 'your_email@example.com',
    domain: 'yourcompany.atlassian.net'
  })
});

const { session_token } = await response.json();
```

### Fetch Jira Projects (JavaScript)

```javascript
// Get Jira projects
const response = await fetch('http://localhost:3001/jira/projects', {
  headers: {
    'Authorization': `Bearer ${session_token}`
  }
});

const { projects } = await response.json();
```

## Architecture

### Session Management

The application uses in-memory session storage for simplicity:
- Sessions are stored in memory and don't persist across restarts
- Session tokens are UUIDs generated for each authentication
- Sessions automatically expire based on configured timeouts
- Expired sessions are cleaned up automatically

### Security Features

- **State Parameter**: OAuth flows use secure state parameters to prevent CSRF attacks
- **Token Validation**: All API endpoints validate session tokens
- **CORS Configuration**: Properly configured CORS for frontend integration
- **Error Handling**: Detailed error responses without exposing sensitive information

### Service Architecture

- **Config Service**: Centralized configuration management
- **Auth Service**: Handles OAuth and API token authentication
- **Atlassian Service**: Integrates with Jira and Confluence APIs
- **Session Storage**: Manages in-memory session data

## Development

### Running Tests

```bash
pytest
```

### Code Quality

```bash
# Run linting
flake8 src/

# Format code
black src/
```

### Generate OpenAPI Schema

```bash
python -m src.api.generate_openapi
```

## Troubleshooting

### Common Issues

1. **"Address already in use" error**: Another process is using port 3001
   ```bash
   lsof -ti:3001 | xargs kill -9
   ```

2. **OAuth callback errors**: Verify redirect URIs match in Atlassian Developer Console

3. **API token authentication fails**: 
   - For Jira: Ensure email is provided with API token
   - For Confluence: Use Personal Access Token (PAT) without email

4. **CORS errors**: Check that frontend origin is in `CORS_ORIGINS` configuration

### Logging

The application uses Python's built-in logging. Logs include:
- Authentication events
- API requests and responses
- Error conditions
- Session management events

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License.
