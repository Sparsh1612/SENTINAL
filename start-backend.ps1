# Start Sentinel Backend (Fixed Import Issues)
Write-Host "Starting Sentinel Backend..." -ForegroundColor Green

# Check if Python is working
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "Python not found in PATH. Trying to find it..." -ForegroundColor Yellow
    
    # Try common Python locations
    $pythonPaths = @(
        "C:\Users\spars\AppData\Local\Programs\Python\Python313\python.exe",
        "C:\Python313\python.exe",
        "C:\Python312\python.exe",
        "C:\Python311\python.exe",
        "C:\Users\spars\AppData\Local\Programs\Python\Python312\python.exe",
        "C:\Users\spars\AppData\Local\Programs\Python\Python311\python.exe"
    )
    
    $pythonExe = $null
    foreach ($path in $pythonPaths) {
        if (Test-Path $path) {
            $pythonExe = $path
            Write-Host "Found Python at: $pythonExe" -ForegroundColor Green
            break
        }
    }
    
    if ($pythonExe) {
        $env:PATH = "$(Split-Path $pythonExe);$env:PATH"
        Write-Host "Added Python to PATH for this session" -ForegroundColor Green
    } else {
        Write-Host "Python not found. Please install Python 3.11+ from python.org" -ForegroundColor Red
        exit 1
    }
}

# Check if virtual environment exists
if (Test-Path "venv") {
    Write-Host "Activating virtual environment..." -ForegroundColor Yellow
    & ".\venv\Scripts\Activate.ps1"
} else {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
    & ".\venv\Scripts\Activate.ps1"
}

# Install requirements
Write-Host "Installing requirements..." -ForegroundColor Yellow
pip install -r requirements.txt

# Set PYTHONPATH to include backend directory
$env:PYTHONPATH = "$PWD\backend;$env:PYTHONPATH"
Write-Host "Set PYTHONPATH: $env:PYTHONPATH" -ForegroundColor Green

# Change to backend directory and run
Write-Host "Starting FastAPI server..." -ForegroundColor Green
Write-Host "Access your API at: http://localhost:8000" -ForegroundColor Cyan
Write-Host "API docs at: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow

cd backend
python run.py
