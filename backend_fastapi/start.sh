#!/bin/bash

# Jira & Confluence Connector - FastAPI Backend Startup Script

echo "🚀 Starting Jira & Confluence Connector API..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run setup first:"
    echo "   python -m venv venv"
    echo "   source venv/bin/activate"
    echo "   pip install -r requirements.txt"
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Copying from .env.example..."
    cp .env.example .env
    echo "📝 Please edit .env with your Atlassian credentials before running again."
    exit 1
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Check if dependencies are installed
echo "📦 Checking dependencies..."
python -c "import fastapi" 2>/dev/null || {
    echo "❌ Dependencies not installed. Installing now..."
    pip install -r requirements.txt
}

# Generate OpenAPI schema
echo "📄 Generating OpenAPI schema..."
python -m src.api.generate_openapi

# Start the server
echo "🌐 Starting FastAPI server on http://localhost:3001"
echo "📚 API Documentation: http://localhost:3001/docs"
echo "🔍 OpenAPI Schema: http://localhost:3001/openapi.json"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

uvicorn src.api.main:app --host 0.0.0.0 --port 3001 --reload
