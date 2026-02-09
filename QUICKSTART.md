# 🚀 RedClaw Quick Start Guide

**5-Minute Setup for Fresh Kali Linux**

---

## ⚡ One-Line Install

```bash
# Clone and install on Kali
git clone https://github.com/your-org/redclaw.git && cd redclaw && ./install.sh
```

---

## 📋 Manual Installation (Step by Step)

### Step 1: Download RedClaw

```bash
# Option A: Git clone
git clone https://github.com/your-org/redclaw.git
cd redclaw

# Option B: Download ZIP
wget https://github.com/your-org/redclaw/archive/main.zip
unzip main.zip && cd redclaw-main
```

### Step 2: Install Dependencies

```bash
# System packages
sudo apt update && sudo apt install -y python3 python3-pip python3-venv

# Python packages
pip3 install -e .
```

### Step 3: Configure LLM Endpoint

```bash
# Set your Kaggle ngrok API endpoint
export REDCLAW_API_URL="https://YOUR-NGROK-URL.ngrok-free.app"

# Or add to ~/.bashrc for persistence
echo 'export REDCLAW_API_URL="https://YOUR-NGROK-URL.ngrok-free.app"' >> ~/.bashrc
source ~/.bashrc
```

### Step 4: Run RedClaw

```bash
# Start CLI
redclaw

# Or with target
redclaw --target 10.10.10.5
```

---

## 🎯 Basic Commands

| Command | Description |
|---------|-------------|
| `target <IP>` | Set target IP/hostname |
| `scan` | Start reconnaissance scan |
| `exploit` | Attempt exploitation |
| `report` | Generate findings report |
| `help` | Show all commands |
| `exit` | Exit RedClaw |

---

## 📖 Usage Examples

### Example 1: Scan a TryHackMe Machine
```
redclaw
> target 10.10.10.5
> scan
> exploit
> report
```

### Example 2: Run Specific Tool
```
redclaw
> nmap -sV -sC 10.10.10.5
> nikto -h 10.10.10.5
```

### Example 3: AI-Assisted Attack
```
redclaw
> Scan this target and find vulnerabilities: 10.10.10.5
> Explain what you found and suggest next steps
```

---

## ❓ Troubleshooting

### Error: "Connection refused"
```bash
# Check if LLM API is running
curl $REDCLAW_API_URL/health
```

### Error: "Module not found"
```bash
# Reinstall dependencies
pip3 install -e .
```

### Error: "Permission denied"
```bash
# Some tools require root
sudo redclaw
```

---

## 📞 Support

- GitHub Issues: https://github.com/your-org/redclaw/issues
- Documentation: See README.md for full details
