# Flask PostgreSQL Chat Application - Quick Start Script
# This script will set up and run the Flask application

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Flask PostgreSQL Chat Application" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if virtual environment exists
if (!(Test-Path ".venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv .venv
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& .\.venv\Scripts\Activate.ps1

# Install/Update dependencies
Write-Host "Installing dependencies..." -ForegroundColor Yellow
pip install -r requirements_flask.txt

# Check if example.env exists
if (!(Test-Path "example.env")) {
    Write-Host "ERROR: example.env file not found!" -ForegroundColor Red
    Write-Host "Please create example.env with your configuration." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Starting Flask Application..." -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "Access the application at: http://localhost:5000" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

# Run the Flask application
python pgtest.py
