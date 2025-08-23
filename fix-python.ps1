# Fix Python Installation for Sentinel
# This script helps resolve Python installation issues on Windows

Write-Host "Fixing Python Installation for Sentinel" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Green

# Check current Python installation
Write-Host "Checking current Python installation..." -ForegroundColor Yellow

$pythonPaths = @(
    "C:\Users\spars\AppData\Local\Programs\Python\Python313\python.exe",
    "C:\Program Files\Python*\python.exe",
    "C:\Users\spars\AppData\Local\Microsoft\WindowsApps\python.exe"
)

$workingPython = $null

foreach ($path in $pythonPaths) {
    if (Test-Path $path) {
        Write-Host "Found Python at: $path" -ForegroundColor Cyan
        try {
            $result = & $path --version 2>&1
            if ($LASTEXITCODE -eq 0) {
                Write-Host "Working Python found: $result" -ForegroundColor Green
                $workingPython = $path
                break
            }
        } catch {
            Write-Host "Python at $path is not working" -ForegroundColor Red
        }
    }
}

if ($workingPython) {
    Write-Host "Using working Python: $workingPython" -ForegroundColor Green
    
    # Add to PATH for current session
    $env:PATH = "$workingPython;$env:PATH"
    
    # Create alias
    Set-Alias -Name python -Value $workingPython
    
    Write-Host "Python is now available as 'python' command" -ForegroundColor Green
    
    # Test it
    Write-Host "Testing Python..." -ForegroundColor Cyan
    python --version
    
} else {
    Write-Host "No working Python found. Here are your options:" -ForegroundColor Red
    
    Write-Host "Option 1: Fix Current Installation" -ForegroundColor Yellow
    Write-Host "   The Python installation at C:\Users\spars\AppData\Local\Programs\Python\Python313\ appears corrupted."
    Write-Host "   Try uninstalling and reinstalling Python 3.13 from the Microsoft Store or python.org"
    
    Write-Host "Option 2: Install Python via winget" -ForegroundColor Yellow
    if (Get-Command winget -ErrorAction SilentlyContinue) {
        Write-Host "   Run: winget install Python.Python.3.11" -ForegroundColor Cyan
    } else {
        Write-Host "   Install winget first, then run the above command" -ForegroundColor Cyan
    }
    
    Write-Host "Option 3: Manual Download" -ForegroundColor Yellow
    Write-Host "   1. Visit https://www.python.org/downloads/" -ForegroundColor White
    Write-Host "   2. Download Python 3.11 or later" -ForegroundColor White
    Write-Host "   3. Run installer and check 'Add Python to PATH'" -ForegroundColor White
    Write-Host "   4. Restart PowerShell" -ForegroundColor White
    
    Write-Host "Alternative: Use Docker Only" -ForegroundColor Yellow
    Write-Host "   If you have Docker working, you can run Sentinel entirely in containers:" -ForegroundColor White
    Write-Host "   docker-compose up -d" -ForegroundColor Cyan
}

Write-Host "Quick Test:" -ForegroundColor Green
Write-Host "After fixing Python, test with: python --version" -ForegroundColor Cyan
Write-Host "Then run: .\setup-sentinel.ps1" -ForegroundColor Cyan
