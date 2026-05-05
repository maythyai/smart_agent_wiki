#!/bin/bash
#
# Quick installer redirect for get.saw.sh domain
# This script redirects to the main installer
#
# Usage:
#   curl -fsSL https://get.saw.sh | bash
#   curl -fsSL https://get.saw.sh/ps1 | bash  # Windows PowerShell
#

set -e

# Main installer URL
INSTALLER_URL="https://raw.githubusercontent.com/chensaics/smart_agent_wiki/master/scripts/install.sh"
POWERSHELL_URL="https://raw.githubusercontent.com/chensaics/smart_agent_wiki/master/scripts/install.ps1"

# Check if user wants PowerShell version
if [ "$1" = "ps1" ] || [ "$1" = "powershell" ]; then
    echo "# Run this command in PowerShell:"
    echo "iwr -useb $POWERSHELL_URL | iex"
    exit 0
fi

# Download and execute main installer
echo "Downloading Smart Agent Wiki installer..."
exec bash -c "$(curl -fsSL $INSTALLER_URL)"
