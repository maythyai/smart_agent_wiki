# Smart Agent Wiki Installer for Windows
# https://github.com/chensaics/smart_agent_wiki
#
# Usage:
#   iwr -useb https://raw.githubusercontent.com/chensaics/smart_agent_wiki/master/scripts/install.ps1 | iex
#
# License: MIT

$ErrorActionPreference = "Stop"
$ScriptVersion = "1.0.0"

# Logging functions
function Write-Info {
    param($msg)
    Write-Host "[INFO] " -ForegroundColor Blue -NoNewline
    Write-Host $msg
}

function Write-Success {
    param($msg)
    Write-Host "[OK] " -ForegroundColor Green -NoNewline
    Write-Host $msg
}

function Write-Warn {
    param($msg)
    Write-Host "[WARN] " -ForegroundColor Yellow -NoNewline
    Write-Host $msg
}

function Write-Err {
    param($msg)
    Write-Host "[ERROR] " -ForegroundColor Red -NoNewline
    Write-Host $msg
    exit 1
}

# Detect architecture
function Get-Architecture {
    $arch = $env:PROCESSOR_ARCHITECTURE
    switch ($arch) {
        "AMD64" { return "x64" }
        "ARM64" { return "arm64" }
        default { return "unknown" }
    }
}

# Check Python installation
function Check-Python {
    Write-Info "Checking Python installation..."

    $pythonCmds = @("python", "python3")
    $foundPython = $null
    $version = $null

    foreach ($cmd in $pythonCmds) {
        try {
            $output = & $cmd --version 2>&1
            if ($output -match "Python (\d+)\.(\d+)") {
                $major = [int]$Matches[1]
                $minor = [int]$Matches[2]
                $version = "$major.$minor"
                $foundPython = $cmd
                break
            }
        }
        catch {
            continue
        }
    }

    if (-not $foundPython) {
        Write-Err "Python not found. Please install Python 3.11+ from https://www.python.org/downloads/"
        return $null
    }

    if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 11)) {
        Write-Err "Python $version found. Smart Agent Wiki requires Python 3.11+"
        Write-Info "Please upgrade: https://www.python.org/downloads/"
        return $null
    }

    Write-Success "Python $version detected ($foundPython)"
    return $foundPython
}

# Check pip availability
function Check-Pip {
    param($pythonCmd)

    Write-Info "Checking pip..."

    try {
        & $pythonCmd -m pip --version | Out-Null
        Write-Success "pip is available"
        return $true
    }
    catch {
        Write-Err "pip not found. Please install pip:"
        Write-Info "  $pythonCmd -m ensurepip --upgrade"
        return $false
    }
}

# Check pipx availability
function Test-Pipx {
    try {
        Get-Command pipx -ErrorAction Stop | Out-Null
        return $true
    }
    catch {
        return $false
    }
}

# Install via pipx
function Install-ViaPipx {
    Write-Info "Installing via pipx (isolated environment)..."

    pipx install smart-agent-wiki

    Write-Success "Installation complete!"
}

# Install via pip
function Install-ViaPip {
    param($pythonCmd)

    Write-Info "Installing via pip..."
    Write-Info "Tip: Install pipx for better isolation: pip install pipx"
    Write-Host ""

    & $pythonCmd -m pip install --user smart-agent-wiki

    # Check PATH
    $userScripts = Join-Path $env:APPDATA "Python\Python311\Scripts"
    if (-not ($env:PATH -like "*$userScripts*")) {
        Write-Warn "Please add Python Scripts to your PATH:"
        Write-Host "  $userScripts"
    }

    Write-Success "Installation complete!"
}

# Verify installation
function Verify-Installation {
    Write-Info "Verifying installation..."
    Write-Host ""

    try {
        $saw = Get-Command saw -ErrorAction Stop
        $version = & saw --version 2>$null

        Write-Success "Smart Agent Wiki $version installed successfully!"
        Write-Host ""
        Write-Host "Quick Start:" -ForegroundColor White
        Write-Host ""
        Write-Host "  saw init          # Create a new wiki"
        Write-Host "  saw ingest .      # Ingest documents"
        Write-Host "  saw query 'topic' # Search your wiki"
        Write-Host "  saw web           # Start web UI"
        Write-Host ""
        Write-Host "Documentation: " -NoNewline
        Write-Host "https://github.com/chensaics/smart_agent_wiki" -ForegroundColor Cyan
        Write-Host ""
        return $true
    }
    catch {
        Write-Warn "saw command not found in PATH"
        Write-Info "You may need to:"
        Write-Info "  1. Restart your terminal"
        Write-Info "  2. Add Python Scripts to your PATH"
        return $false
    }
}

# Print banner
function Print-Banner {
    Write-Host ""
    Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor White
    Write-Host "  Smart Agent Wiki Installer v$ScriptVersion" -ForegroundColor White
    Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor White
    Write-Host ""
}

# Main installation flow
function Main {
    Print-Banner

    # Detect environment
    $arch = Get-Architecture
    Write-Info "Detected: Windows ($arch)"
    Write-Host ""

    # Check Python
    $pythonCmd = Check-Python
    if (-not $pythonCmd) {
        exit 1
    }

    # Check pip
    if (-not (Check-Pip $pythonCmd)) {
        exit 1
    }

    Write-Host ""

    # Install - prefer pipx for isolation
    if (Test-Pipx) {
        Install-ViaPipx
    }
    else {
        Install-ViaPip $pythonCmd
    }

    Write-Host ""

    # Verify
    Verify-Installation
}

# Run main
Main
