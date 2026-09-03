#!/usr/bin/env bash
#
# Smart Agent Wiki Installer
# https://github.com/chensaics/smart_agent_wiki
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/chensaics/smart_agent_wiki/master/scripts/install.sh | bash
#
# License: MIT

set -e

# Version
SAW_VERSION="1.2.0"
SCRIPT_VERSION="1.0.0"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Logging functions
info() { echo -e "${BLUE}[INFO]${NC} $1"; }
success() { echo -e "${GREEN}[OK]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

# Detect operating system
detect_os() {
    case "$(uname -s)" in
        Linux*)  echo "linux";;
        Darwin*) echo "macos";;
        CYGWIN*|MINGW*|MSYS*) echo "windows";;
        *)       echo "unknown";;
    esac
}

# Detect architecture
detect_arch() {
    case "$(uname -m)" in
        x86_64|amd64)  echo "x64";;
        arm64|aarch64) echo "arm64";;
        armv7l)        echo "arm";;
        *)             echo "unknown";;
    esac
}

# Check Python installation and version
check_python() {
    local min_major=3
    local min_minor=11

    info "Checking Python installation..."

    # Try python3 first, then python
    local python_cmd=""
    if command -v python3 &> /dev/null; then
        python_cmd="python3"
    elif command -v python &> /dev/null; then
        python_cmd="python"
    else
        error "Python not found. Please install Python 3.11+ and try again."
        info "Download from: https://www.python.org/downloads/"
        return 1
    fi

    # Get version
    local version=$($python_cmd -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>/dev/null)
    if [ -z "$version" ]; then
        error "Failed to detect Python version"
        return 1
    fi

    local major=$(echo "$version" | cut -d. -f1)
    local minor=$(echo "$version" | cut -d. -f2)

    if [ "$major" -lt "$min_major" ] || { [ "$major" -eq "$min_major" ] && [ "$minor" -lt "$min_minor" ]; }; then
        error "Python $version found. Smart Agent Wiki requires Python 3.11+"
        info "Please upgrade Python: https://www.python.org/downloads/"
        return 1
    fi

    success "Python $version detected ($python_cmd)"
    echo "$python_cmd"
    return 0
}

# Check pip availability
check_pip() {
    local python_cmd="$1"

    info "Checking pip..."

    if $python_cmd -m pip --version &> /dev/null; then
        success "pip is available"
        return 0
    elif command -v pip3 &> /dev/null; then
        success "pip3 is available"
        return 0
    elif command -v pip &> /dev/null; then
        success "pip is available"
        return 0
    else
        error "pip not found. Please install pip:"
        info "  curl -fsSL https://bootstrap.pypa.io/get-pip.py | $python_cmd"
        return 1
    fi
}

# Check pipx availability
check_pipx() {
    if command -v pipx &> /dev/null; then
        return 0
    else
        return 1
    fi
}

# Install via pipx (preferred method)
install_via_pipx() {
    info "Installing via pipx (isolated environment)..."

    pipx install smart-agent-wiki

    # Ensure PATH includes pipx bin
    local pipx_bin=$(pipx environment --value PIPX_BIN_DIR 2>/dev/null || echo "$HOME/.local/bin")
    if [[ ":$PATH:" != *":$pipx_bin:"* ]]; then
        warn "Please add pipx bin directory to your PATH:"
        echo ""
        echo "  export PATH=\"\$PATH:$pipx_bin\""
        echo ""
        info "Add this line to your ~/.bashrc or ~/.zshrc"
    fi

    return 0
}

# Install via pip --user
install_via_pip() {
    local python_cmd="$1"

    info "Installing via pip..."

    $python_cmd -m pip install --user --upgrade smart-agent-wiki

    # Check if user bin is in PATH
    local user_base=$($python_cmd -m site --user-base 2>/dev/null)
    local bin_path="$user_base/bin"

    if [[ ":$PATH:" != *":$bin_path:"* ]]; then
        warn "The user bin directory is not in PATH. Add it:"
        echo ""
        echo "  export PATH=\"\$PATH:$bin_path\""
        echo ""
        info "Add this line to your ~/.bashrc or ~/.zshrc"
    fi

    return 0
}

# Verify installation
verify_installation() {
    info "Verifying installation..."

    # Try to find saw command
    local saw_cmd=""
    if command -v saw &> /dev/null; then
        saw_cmd="saw"
    elif [ -f "$HOME/.local/bin/saw" ]; then
        saw_cmd="$HOME/.local/bin/saw"
    fi

    if [ -n "$saw_cmd" ]; then
        local version=$($saw_cmd --version 2>/dev/null || echo "installed")
        success "Smart Agent Wiki v$version installed successfully!"
        echo ""
        echo -e "${BOLD}Quick Start:${NC}"
        echo ""
        echo "  saw init          # Create a new wiki"
        echo "  saw ingest .      # Ingest documents"
        echo "  saw query 'topic' # Search your wiki"
        echo "  saw web           # Start web UI"
        echo ""
        echo -e "${BOLD}Documentation:${NC} https://github.com/chensaics/smart_agent_wiki"
        echo ""
        return 0
    else
        warn "saw command not found in PATH"
        info "You may need to:"
        info "  1. Restart your shell/terminal"
        info "  2. Add ~/.local/bin to your PATH"
        return 1
    fi
}

# Print banner
print_banner() {
    echo ""
    echo -e "${BOLD}═══════════════════════════════════════════════════════${NC}"
    echo -e "${BOLD}  Smart Agent Wiki Installer v$SCRIPT_VERSION${NC}"
    echo -e "${BOLD}═══════════════════════════════════════════════════════${NC}"
    echo ""
}

# Main installation flow
main() {
    print_banner

    # Detect environment
    local os=$(detect_os)
    local arch=$(detect_arch)
    info "Detected: $os ($arch)"
    echo ""

    # Check Python
    local python_cmd=$(check_python)
    if [ $? -ne 0 ]; then
        exit 1
    fi

    # Check pip
    check_pip "$python_cmd"
    if [ $? -ne 0 ]; then
        exit 1
    fi

    echo ""

    # Install - prefer pipx for isolation
    if check_pipx; then
        install_via_pipx
    else
        info "pipx not found, using pip --user"
        info "Tip: Install pipx for better isolation: pip install pipx"
        echo ""
        install_via_pip "$python_cmd"
    fi

    echo ""

    # Verify
    verify_installation
}

# Run main
main "$@"
