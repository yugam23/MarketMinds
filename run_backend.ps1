# MarketMinds Startup Script
Write-Host "Starting MarketMinds Backend..." -ForegroundColor Blue

# Navigate to server directory
Set-Location -Path "$PSScriptRoot/server"

# Run with virtual environment python
.\venv\Scripts\python.exe -m uvicorn main:app --reload
