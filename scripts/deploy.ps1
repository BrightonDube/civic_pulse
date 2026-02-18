# CivicPulse Railway Deployment Script (PowerShell)
# Usage: .\scripts\deploy.ps1 [backend|frontend|all]

param(
    [Parameter(Position=0)]
    [ValidateSet("backend", "frontend", "all", "status", "logs", "help")]
    [string]$Command = "all"
)

$ErrorActionPreference = "Stop"

function Write-Status($message) {
    Write-Host "[INFO] $message" -ForegroundColor Blue
}

function Write-Success($message) {
    Write-Host "[SUCCESS] $message" -ForegroundColor Green
}

function Write-Warning($message) {
    Write-Host "[WARNING] $message" -ForegroundColor Yellow
}

function Write-Error($message) {
    Write-Host "[ERROR] $message" -ForegroundColor Red
}

function Test-RailwayCLI {
    try {
        $null = Get-Command railway -ErrorAction Stop
        return $true
    } catch {
        Write-Error "Railway CLI is not installed."
        Write-Host "Install it with: npm install -g @railway/cli"
        exit 1
    }
}

function Test-RailwayAuth {
    try {
        $result = railway whoami 2>&1
        if ($LASTEXITCODE -ne 0) {
            throw "Not authenticated"
        }
    } catch {
        Write-Error "Not authenticated with Railway."
        Write-Host "Run: railway login"
        exit 1
    }
}

function Deploy-Backend {
    Write-Status "Deploying backend to Railway..."
    
    Push-Location $PSScriptRoot\..
    
    try {
        railway up --service backend --path-as-root backend --detach
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Backend deployment initiated!"
            Write-Host "View logs: railway logs --service backend"
        } else {
            throw "Deployment failed"
        }
    } catch {
        Write-Error "Backend deployment failed!"
        Pop-Location
        exit 1
    }
    
    Pop-Location
}

function Deploy-Frontend {
    Write-Status "Deploying frontend to Railway..."
    
    Push-Location $PSScriptRoot\..
    
    try {
        railway up --service frontend --detach
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Frontend deployment initiated!"
            Write-Host "View logs: railway logs --service frontend"
        } else {
            throw "Deployment failed"
        }
    } catch {
        Write-Error "Frontend deployment failed!"
        Pop-Location
        exit 1
    }
    
    Pop-Location
}

function Deploy-All {
    Write-Status "Deploying both backend and frontend..."
    
    Deploy-Backend
    Write-Host ""
    Deploy-Frontend
    
    Write-Host ""
    Write-Success "All deployments initiated!"
}

function Show-Status {
    Write-Status "Checking deployment status..."
    
    Push-Location $PSScriptRoot\..
    
    Write-Host ""
    Write-Host "=== Backend Status ===" -ForegroundColor Cyan
    railway status --service backend 2>$null
    if ($LASTEXITCODE -ne 0) { Write-Host "Unable to fetch backend status" }
    
    Write-Host ""
    Write-Host "=== Frontend Status ===" -ForegroundColor Cyan
    railway status --service frontend 2>$null
    if ($LASTEXITCODE -ne 0) { Write-Host "Unable to fetch frontend status" }
    
    Pop-Location
}

function Show-Logs {
    Write-Status "Fetching recent logs..."
    
    Push-Location $PSScriptRoot\..
    
    Write-Host ""
    Write-Host "=== Backend Logs (last 20 lines) ===" -ForegroundColor Cyan
    railway logs --service backend --tail 20 2>$null
    if ($LASTEXITCODE -ne 0) { Write-Host "Unable to fetch backend logs" }
    
    Write-Host ""
    Write-Host "=== Frontend Logs (last 20 lines) ===" -ForegroundColor Cyan
    railway logs --service frontend --tail 20 2>$null
    if ($LASTEXITCODE -ne 0) { Write-Host "Unable to fetch frontend logs" }
    
    Pop-Location
}

function Show-Help {
    Write-Host "CivicPulse Railway Deployment Script" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Usage: .\deploy.ps1 [command]"
    Write-Host ""
    Write-Host "Commands:"
    Write-Host "  backend   Deploy only the backend service"
    Write-Host "  frontend  Deploy only the frontend service"
    Write-Host "  all       Deploy both backend and frontend (default)"
    Write-Host "  status    Show deployment status"
    Write-Host "  logs      Show recent logs for both services"
    Write-Host "  help      Show this help message"
    Write-Host ""
    Write-Host "Examples:"
    Write-Host "  .\deploy.ps1 backend    # Deploy backend only"
    Write-Host "  .\deploy.ps1 all        # Deploy everything"
    Write-Host "  .\deploy.ps1 status     # Check deployment status"
}

# Main script
Test-RailwayCLI
Test-RailwayAuth

switch ($Command) {
    "backend"  { Deploy-Backend }
    "frontend" { Deploy-Frontend }
    "all"      { Deploy-All }
    "status"   { Show-Status }
    "logs"     { Show-Logs }
    "help"     { Show-Help }
}
