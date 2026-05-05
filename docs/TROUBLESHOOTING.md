# Troubleshooting Guide

This guide helps you resolve common issues with Smart Agent Wiki.

## Table of Contents

1. [Installation Issues](#installation-issues)
2. [Configuration Issues](#configuration-issues)
3. [Ingest Issues](#ingest-issues)
4. [Query Issues](#query-issues)
5. [Database Issues](#database-issues)
6. [Web UI Issues](#web-ui-issues)
7. [MCP Server Issues](#mcp-server-issues)

---

## Installation Issues

### Error: Python version not supported

**Symptom:**
```
Error: Python 3.11+ required, found 3.8
```

**Solution:**

```bash
# Using pyenv (recommended)
pyenv install 3.11
pyenv global 3.11

# Using conda
conda install python=3.11

# Using system package manager (Ubuntu)
sudo apt update && sudo apt install python3.11
```

---

### Error: pipx not found

**Symptom:**
```
pipx: command not found
```

**Solution:**

```bash
# macOS
brew install pipx
pipx ensurepath

# Linux (pip)
pip install pipx
pipx ensurepath

# Linux (apt)
sudo apt install pipx
```

---

### Error: Permission denied during installation

**Symptom:**
```
PermissionError: [Errno 13] Permission denied: '/usr/local/bin/saw'
```

**Solution:**

```bash
# Use pipx instead (recommended)
pipx install smart-agent-wiki

# Or use --user flag with pip
pip install --user smart-agent-wiki
```

---

### Error: Homebrew installation fails

**Symptom:**
```
Error: Formula not found
```

**Solution:**

```bash
# Tap the repository first
brew tap chensaics/saw
brew install saw

# Or use the direct formula
brew install --formula https://raw.githubusercontent.com/chensaics/smart_agent_wiki/main/homebrew/saw.rb
```

---

## Configuration Issues

### Error: Config file not found

**Symptom:**
```
Config file 'saw.json' not found in current directory
```

**Solution:**

```bash
# Initialize wiki first
saw init

# Or specify config path
saw config --path ./my-wiki/saw.json
```

---

### Error: Invalid LLM provider

**Symptom:**
```
Error: Unknown LLM provider: 'custom'
```

**Solution:**

Supported providers: `local`, `openai`, `anthropic`, `auto`

```bash
# Edit configuration
saw config

# Or set provider explicitly
saw config --set llm.provider=openai
```

---

### Error: API key not set

**Symptom:**
```
Error: OpenAI API key not configured
```

**Solution:**

```bash
# Interactive configuration
saw config

# Or set via environment variable
export OPENAI_API_KEY="sk-..."

# Or set in config file
saw config --set llm.api_key="sk-..."
```

---

## Ingest Issues

### Error: File format not supported

**Symptom:**
```
Error: Unsupported format: .xyz
```

**Solution:**

Supported formats: `.md`, `.pdf`, `.py`, `.js`, `.ts`, `.html`, `.json`, `.yaml`

```bash
# Check supported formats
saw ingest --help

# Use --format to override detection
saw ingest file.xyz --format md
```

---

### Error: File not found

**Symptom:**
```
❌ Error: File 'document.pdf' not found

💡 Suggestions:
  • Check if the file exists: ls document.pdf
  • Use absolute path: saw ingest /path/to/document.pdf
  • Ingest entire directory: saw ingest ./documents/
```

**Solution:**

```bash
# Use absolute path
saw ingest /full/path/to/document.pdf

# Or navigate to the file location
cd /path/to/documents
saw ingest document.pdf
```

---

### Error: PDF parsing failed

**Symptom:**
```
Error: Failed to extract text from PDF
```

**Solution:**

```bash
# Install PDF dependencies
pip install pypdf pdfplumber

# Check PDF is not encrypted
# If encrypted, remove password or use different file
```

---

## Query Issues

### Error: No results found

**Symptom:**
```
Query returned 0 results
```

**Solution:**

```bash
# Check wiki status
saw status

# Verify data was ingested
saw status --verbose

# Try different query modes
saw query "term" --mode direct
saw query "term" --mode graph
saw query "term" --mode reasoning

# Use broader search terms
saw search "partial_term"
```

---

### Error: Query timeout

**Symptom:**
```
Error: Query timed out after 30 seconds
```

**Solution:**

```bash
# Reduce max results
saw query "term" --max-results 10

# Use simpler mode
saw query "term" --mode direct

# Check database size
saw status
```

---

## Database Issues

### Error: Database locked

**Symptom:**
```
sqlite3.OperationalError: database is locked
```

**Solution:**

```bash
# Check for running processes
ps aux | grep saw

# Kill stale processes if needed
kill <pid>

# Remove lock files (safe if no active process)
rm -f .saw/*.lock

# Restart the operation
saw ingest document.pdf
```

---

### Error: Database corrupted

**Symptom:**
```
sqlite3.DatabaseError: database disk image is malformed
```

**Solution:**

```bash
# Backup wiki data
cp -r vault/ vault_backup/
cp -r wiki/ wiki_backup/

# Rebuild database
saw init --rebuild

# Re-ingest from vault
saw ingest vault_backup/ --recursive
```

---

### Error: Database too large

**Symptom:**
```
Warning: Database exceeds 1GB, queries may be slow
```

**Solution:**

```bash
# Check database size
saw status --verbose

# Archive old claims
saw audit --archive --older-than 365d

# Optimize database
saw lint --fix --optimize
```

---

## Web UI Issues

### Error: Web UI not starting

**Symptom:**
```
Error: Port 8000 already in use
```

**Solution:**

```bash
# Use different port
saw web --port 8080

# Check what's using the port
lsof -i :8000

# Kill the process if needed
kill <pid>
```

---

### Error: Web UI shows blank page

**Symptom:**
```
Browser displays blank page at http://localhost:8000
```

**Solution:**

```bash
# Check if backend is running
curl http://localhost:8000/api/status

# Restart web UI
saw web --restart

# Check browser console for errors
# Open Developer Tools → Console tab
```

---

### Error: WebSocket connection failed

**Symptom:**
```
WebSocket connection to ws://localhost:8000/ws failed
```

**Solution:**

```bash
# Check firewall settings
# Allow WebSocket connections

# Use polling fallback (in config)
saw config --set web.websocket=false
```

---

## MCP Server Issues

### Error: MCP server not responding

**Symptom:**
```
Error: MCP server timed out
```

**Solution:**

```bash
# Check MCP server status
saw mcp status

# Restart MCP server
saw mcp restart

# Check logs
saw mcp logs --tail 50
```

---

### Error: MCP tool not found

**Symptom:**
```
Error: Tool 'saw_query' not available
```

**Solution:**

```bash
# List available MCP tools
saw mcp tools

# Verify MCP server is running
saw mcp status

# Check Claude Code configuration
# Ensure MCP server is registered in Claude settings
```

---

## Getting Help

If this guide doesn't resolve your issue:

1. **Check logs:** `saw status --verbose` or `saw audit --tail 100`
2. **Search issues:** https://github.com/chensaics/smart_agent_wiki/issues
3. **Ask community:** https://github.com/chensaics/smart_agent_wiki/discussions
4. **Report bug:** https://github.com/chensaics/smart_agent_wiki/issues/new

---

*Last updated: 2026-05-05*