#!/bin/bash

# ===============================================
# AI RESUME BUILDER - START SERVER SCRIPT
# ===============================================
# This script starts the FastAPI backend server

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check if virtual environment exists
check_venv() {
    if [ ! -d "venv" ]; then
        print_warning "Virtual environment not found. Creating one..."
        python3 -m venv venv
        print_success "Virtual environment created"
    fi
}

# Activate virtual environment and install dependencies
setup_environment() {
    print_status "Activating virtual environment..."
    source venv/bin/activate
    
    print_status "Installing/updating dependencies..."
    pip install -r requirements.txt
    
    if [ $? -eq 0 ]; then
        print_success "Dependencies installed successfully"
    else
        print_error "Failed to install dependencies"
        exit 1
    fi
}

# Check if port is already in use
check_port() {
    local port=8000
    if lsof -ti:$port > /dev/null 2>&1; then
        print_warning "Port $port is already in use"
        print_status "Killing existing process..."
        lsof -ti:$port | xargs kill -9
        sleep 2
        print_success "Port cleared"
    fi
}

# Start the server
start_server() {
    print_status "Starting FastAPI server..."
    print_status "Server will be available at: http://localhost:8000"
    print_status "API Documentation: http://localhost:8000/docs"
    print_status "Health Check: http://localhost:8000/health"
    echo
    print_success "Press Ctrl+C to stop the server"
    echo
    
    # Activate virtual environment and start server
    source venv/bin/activate
    python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
}

# Main execution
main() {
    echo -e "${BLUE}============================================${NC}"
    echo -e "${BLUE}   AI RESUME BUILDER - BACKEND SERVER    ${NC}"
    echo -e "${BLUE}============================================${NC}"
    echo
    
    # Check if we're in the right directory
    if [ ! -f "app/main.py" ]; then
        print_error "app/main.py not found. Please run this script from the project root directory."
        exit 1
    fi
    
    # Check if requirements.txt exists
    if [ ! -f "requirements.txt" ]; then
        print_error "requirements.txt not found. Please ensure you're in the correct directory."
        exit 1
    fi
    
    check_venv
    setup_environment
    check_port
    start_server
}

# Run main function
main