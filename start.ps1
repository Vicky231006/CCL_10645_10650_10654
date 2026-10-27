<#
.SYNOPSIS
  Start Resumo (FastAPI backend + Vite frontend) together.

.DESCRIPTION
  Launches both services in separate windows and waits until each responds.
  Backend:  http://localhost:8000  (docs at /api/docs)
  Frontend: http://localhost:5173

.PARAMETER Stop
  Stop any running Resumo backend/frontend instead of starting them.

.PARAMETER BackendPort
  Backend port. Default 8000.

.PARAMETER FrontendPort
  Frontend port. Default 5173.

.PARAMETER NoWait
  Do not wait for the services to become healthy before returning.

.PARAMETER SeedDemo
  Seed a fully-populated demo account (from the bundled resume) before starting,
  then print its login. Safe to run repeatedly (it resets the demo account only).

.EXAMPLE
  .\start.ps1
  .\start.ps1 -SeedDemo
  .\start.ps1 -Stop
#>
[CmdletBinding()]
param(
    [switch]$Stop,
    [int]$BackendPort = 8000,
    [int]$FrontendPort = 5173,
    [switch]$NoWait,
    [switch]$SeedDemo
)

$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot
$BackendDir = Join-Path $Root "backend"
$FrontendDir = Join-Path $Root "frontend"
$VenvPython = Join-Path $BackendDir ".venv\Scripts\python.exe"

function Write-Section($text) { Write-Host "`n== $text ==" -ForegroundColor Cyan }
function Write-Ok($text) { Write-Host "  [ok] $text" -ForegroundColor Green }
function Write-Warn2($text) { Write-Host "  [!] $text" -ForegroundColor Yellow }
function Write-Err2($text) { Write-Host "  [x] $text" -ForegroundColor Red }

function Stop-PortListeners {
    param([int[]]$Ports)
    foreach ($port in $Ports) {
        $conns = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
        foreach ($c in $conns) {
            $proc = Get-Process -Id $c.OwningProcess -ErrorAction SilentlyContinue
            if ($proc) {
                Write-Warn2 "Stopping $($proc.ProcessName) (pid $($proc.Id)) on port $port"
                Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
            }
        }
    }
}

function Wait-Http {
    param([string]$Url, [int]$TimeoutSeconds = 60)
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        try {
            $r = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 3
            if ($r.StatusCode -ge 200 -and $r.StatusCode -lt 500) { return $true }
        } catch {
            Start-Sleep -Milliseconds 700
        }
    }
    return $false
}

if ($Stop) {
    Write-Section "Stopping Resumo services"
    Stop-PortListeners -Ports @($BackendPort, $FrontendPort)
    Write-Ok "Done."
    return
}

Write-Section "Resumo launcher"

# --- Preflight -------------------------------------------------------------
if (-not (Test-Path -LiteralPath $BackendDir)) { Write-Err2 "backend/ not found"; exit 1 }
if (-not (Test-Path -LiteralPath $FrontendDir)) { Write-Err2 "frontend/ not found"; exit 1 }

if (-not (Test-Path -LiteralPath $VenvPython)) {
    Write-Err2 "Backend virtualenv missing at $VenvPython"
    Write-Host "      Create it with:" -ForegroundColor Gray
    Write-Host "        cd backend" -ForegroundColor Gray
    Write-Host "        python -m venv .venv" -ForegroundColor Gray
    Write-Host "        .\.venv\Scripts\python.exe -m pip install -r requirements.txt" -ForegroundColor Gray
    exit 1
}
Write-Ok "Backend venv found"

if (-not (Test-Path -LiteralPath (Join-Path $FrontendDir "node_modules"))) {
    Write-Warn2 "frontend/node_modules missing - running 'npm install'..."
    Push-Location $FrontendDir
    try { npm install } finally { Pop-Location }
}
Write-Ok "Frontend dependencies present"

# Free any stale listeners.
Stop-PortListeners -Ports @($BackendPort, $FrontendPort)

# --- Optional: seed demo account ------------------------------------------
if ($SeedDemo) {
    Write-Section "Seeding demo account"
    Push-Location $BackendDir
    try {
        & $VenvPython "scripts\seed_demo.py"
        if ($LASTEXITCODE -ne 0) { Write-Warn2 "Demo seed failed (exit $LASTEXITCODE); continuing without it." }
    } finally {
        Pop-Location
    }
}

# --- Launch backend --------------------------------------------------------
Write-Section "Starting backend on :$BackendPort"
$backendCmd = "`$host.UI.RawUI.WindowTitle='Resumo API'; " +
    "& '$VenvPython' -m uvicorn app.main:app --reload --host 127.0.0.1 --port $BackendPort"
Start-Process -FilePath "powershell" -ArgumentList "-NoExit", "-Command", $backendCmd -WorkingDirectory $BackendDir

# --- Launch frontend -------------------------------------------------------
Write-Section "Starting frontend on :$FrontendPort"
$frontendCmd = "`$host.UI.RawUI.WindowTitle='Resumo Web'; npm run dev -- --port $FrontendPort --strictPort"
Start-Process -FilePath "powershell" -ArgumentList "-NoExit", "-Command", $frontendCmd -WorkingDirectory $FrontendDir

if ($NoWait) {
    Write-Ok "Services launched (not waiting)."
    return
}

# --- Health checks ---------------------------------------------------------
Write-Section "Waiting for services"

$backendUrl = "http://127.0.0.1:$BackendPort/api/v1/health"
if (Wait-Http -Url $backendUrl -TimeoutSeconds 60) {
    Write-Ok "Backend healthy: $backendUrl"
} else {
    Write-Err2 "Backend did not become healthy in time. Check the 'Resumo API' window."
}

$frontendUrl = "http://127.0.0.1:$FrontendPort/"
if (Wait-Http -Url $frontendUrl -TimeoutSeconds 60) {
    Write-Ok "Frontend healthy: $frontendUrl"
} else {
    Write-Warn2 "Frontend not responding yet. Check the 'Resumo Web' window (Vite may still be compiling)."
}

Write-Section "Resumo is running"
Write-Host "  Web app   : http://localhost:$FrontendPort" -ForegroundColor White
Write-Host "  API       : http://localhost:$BackendPort" -ForegroundColor White
Write-Host "  API docs  : http://localhost:$BackendPort/api/docs" -ForegroundColor White
if ($SeedDemo) {
    Write-Host "`n  Demo login:" -ForegroundColor Cyan
    Write-Host "    email:    demo@resumo.app" -ForegroundColor White
    Write-Host "    password: demo1234" -ForegroundColor White
}
Write-Host "`n  Stop with: .\start.ps1 -Stop" -ForegroundColor Gray
