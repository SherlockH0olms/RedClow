#!/bin/bash
#==============================================================================
# RedClaw v2.0 - Kali Linux Deployment Script
# One-liner installation for production deployment
#==============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Banner
echo -e "${RED}"
cat << 'EOF'
 ____          _  ____ _                   ____  
|  _ \ ___  __| |/ ___| | __ ___      __ _|___ \ 
| |_) / _ \/ _` | |   | |/ _` \ \ /\ / /  __) |
|  _ <  __/ (_| | |___| | (_| |\ V  V /  / __/ 
|_| \_\___|\__,_|\____|_|\__,_| \_/\_/  |_____|

  Autonomous Red Team AI Agent - Kali Deployment
EOF
echo -e "${NC}"

# Variables
INSTALL_DIR="${INSTALL_DIR:-/opt/redclaw}"
VENV_DIR="${INSTALL_DIR}/venv"
DATA_DIR="${INSTALL_DIR}/data"
LOG_DIR="${INSTALL_DIR}/logs"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${YELLOW}[!] Running without root. Some features may be limited.${NC}"
fi

echo -e "${BLUE}[*] Starting RedClaw v2.0 deployment...${NC}"

#------------------------------------------------------------------------------
# 1. System Dependencies
#------------------------------------------------------------------------------
echo -e "${CYAN}[1/6] Installing system dependencies...${NC}"

if command -v apt-get &> /dev/null; then
    sudo apt-get update -qq
    sudo apt-get install -y -qq \
        python3 \
        python3-pip \
        python3-venv \
        git \
        nmap \
        nikto \
        whois \
        dnsutils \
        curl \
        jq \
        subfinder \
        httpx-toolkit \
        2>/dev/null || true
fi

#------------------------------------------------------------------------------
# 2. Create Directory Structure
#------------------------------------------------------------------------------
echo -e "${CYAN}[2/6] Creating directory structure...${NC}"

sudo mkdir -p "$INSTALL_DIR"
sudo mkdir -p "$DATA_DIR"/{memory,rag,reports}
sudo mkdir -p "$LOG_DIR"
sudo mkdir -p "$INSTALL_DIR"/knowledge/{mitre,cve,exploitdb}

# Set permissions if running as root
if [ "$EUID" -eq 0 ]; then
    chown -R $SUDO_USER:$SUDO_USER "$INSTALL_DIR" 2>/dev/null || true
fi

#------------------------------------------------------------------------------
# 3. Clone/Update Repository
#------------------------------------------------------------------------------
echo -e "${CYAN}[3/6] Setting up RedClaw source...${NC}"

if [ -d "$INSTALL_DIR/src" ]; then
    echo -e "${YELLOW}[*] Source exists, updating...${NC}"
    cd "$INSTALL_DIR/src"
    git pull 2>/dev/null || true
else
    echo -e "${YELLOW}[*] Cloning repository...${NC}"
    
    # For local development, copy from current location
    if [ -d "./src/redclaw" ]; then
        cp -r ./src "$INSTALL_DIR/"
    else
        # Clone from GitHub (when available)
        # git clone https://github.com/sparkstack/redclaw.git "$INSTALL_DIR/src"
        mkdir -p "$INSTALL_DIR/src/redclaw"
    fi
fi

#------------------------------------------------------------------------------
# 4. Python Virtual Environment
#------------------------------------------------------------------------------
echo -e "${CYAN}[4/6] Setting up Python environment...${NC}"

python3 -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"

pip install --upgrade pip -q

# Install dependencies
pip install -q \
    httpx \
    rich \
    prompt_toolkit \
    pydantic \
    chromadb \
    msgpack \
    python-dotenv \
    aiofiles \
    networkx

#------------------------------------------------------------------------------
# 5. Configuration
#------------------------------------------------------------------------------
echo -e "${CYAN}[5/6] Creating configuration...${NC}"

# Create config file
cat > "$INSTALL_DIR/config.env" << 'ENVCONFIG'
# RedClaw v2.0 Configuration
# ===========================

# LLM Configuration
# -----------------
# For local Ollama:
# LLM_API_URL=http://localhost:11434/v1
# LLM_MODEL=phi-4

# For Kaggle/External API:
LLM_API_URL=http://localhost:8000/v1
LLM_MODEL=phi-4
LLM_MAX_TOKENS=4096
LLM_TEMPERATURE=0.7

# Paths
# -----
REDCLAW_HOME=/opt/redclaw
REDCLAW_DATA=/opt/redclaw/data
REDCLAW_LOGS=/opt/redclaw/logs

# Engines (optional)
# ------------------
# CALDERA_URL=http://localhost:8888
# CALDERA_KEY=ADMIN123

# MSF_HOST=127.0.0.1
# MSF_PORT=55553
# MSF_USER=msf
# MSF_PASS=msf

# HEXSTRIKE_URL=http://localhost:9999
ENVCONFIG

#------------------------------------------------------------------------------
# 6. Create Launcher Script
#------------------------------------------------------------------------------
echo -e "${CYAN}[6/6] Creating launcher script...${NC}"

cat > "$INSTALL_DIR/redclaw" << 'LAUNCHER'
#!/bin/bash
# RedClaw Launcher

INSTALL_DIR="/opt/redclaw"
source "$INSTALL_DIR/venv/bin/activate"
source "$INSTALL_DIR/config.env" 2>/dev/null || true

export PYTHONPATH="$INSTALL_DIR/src:$PYTHONPATH"

cd "$INSTALL_DIR"

case "$1" in
    "cli"|"")
        python3 -m redclaw.cli.app
        ;;
    "recon")
        python3 -c "
from redclaw import RedClawLLM, ReconAgent
import asyncio

async def main():
    llm = RedClawLLM()
    agent = ReconAgent(llm)
    result = await agent.execute('$2')
    print(result)

asyncio.run(main())
"
        ;;
    "test")
        python3 -c "
from redclaw import RedClawLLM
llm = RedClawLLM()
ok = llm.health_check()
print('✓ LLM Connected' if ok else '✗ LLM Not Available')
"
        ;;
    "version")
        python3 -c "from redclaw import __version__; print(f'RedClaw v{__version__}')"
        ;;
    "help"|"-h"|"--help")
        echo "Usage: redclaw [command] [args]"
        echo ""
        echo "Commands:"
        echo "  cli        Start interactive CLI (default)"
        echo "  recon      Run reconnaissance on target"
        echo "  test       Test LLM connection"
        echo "  version    Show version"
        echo "  help       Show this help"
        ;;
    *)
        echo "Unknown command: $1"
        echo "Use 'redclaw help' for usage"
        ;;
esac
LAUNCHER

chmod +x "$INSTALL_DIR/redclaw"

# Create symlink
if [ "$EUID" -eq 0 ]; then
    ln -sf "$INSTALL_DIR/redclaw" /usr/local/bin/redclaw
fi

#------------------------------------------------------------------------------
# Complete
#------------------------------------------------------------------------------
echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║          RedClaw v2.0 Installation Complete!               ║${NC}"
echo -e "${GREEN}╠════════════════════════════════════════════════════════════╣${NC}"
echo -e "${GREEN}║ Installation: $INSTALL_DIR${NC}"
echo -e "${GREEN}║                                                            ║${NC}"
echo -e "${GREEN}║ Quick Start:                                               ║${NC}"
echo -e "${GREEN}║   1. Configure LLM:  nano $INSTALL_DIR/config.env${NC}"
echo -e "${GREEN}║   2. Launch CLI:     redclaw                               ║${NC}"
echo -e "${GREEN}║   3. Test connection: redclaw test                         ║${NC}"
echo -e "${GREEN}║                                                            ║${NC}"
echo -e "${GREEN}║ For external LLM (Kaggle Phi-4):                          ║${NC}"
echo -e "${GREEN}║   - Start ngrok tunnel from Kaggle notebook               ║${NC}"
echo -e "${GREEN}║   - Update LLM_API_URL in config.env                      ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Deactivate venv
deactivate 2>/dev/null || true

exit 0
