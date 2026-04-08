# SpectreMind

SpectreMind is a local-first modular security research and authorized red-team assistant built as a controlled operator system, not an autonomous black box.

The current version focuses on a clean execution spine:

User input → task planning → scope validation → tool execution → parsing → storage → reporting

It is designed to be transparent, session-based, and extensible, so every action can be inspected, logged, and improved over time.

## Current Capabilities

- Session-based task execution
- Controlled orchestration with AETHER
- Nmap wrapper integration for recon
- Structured parsing of Nmap output
- SQLite storage for sessions, tasks, tool runs, and findings
- Markdown report generation with SCRIBE
- Event logging with per-session trace history
- Basic natural language task handling through `ask`
- Scope validation and approval gating

## Architecture

SpectreMind currently works through this flow:

```text
User / CLI
   ↓
Task Creation
   ↓
AETHER Planning
   ↓
Scope Validation
   ↓
Tool Execution
   ↓
Output Parsing
   ↓
SQLite Storage
   ↓
SCRIBE Reporting
   ↓
CLI Output / Session Artifacts
Project Structure
spectremind/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── schemas/
│   ├── core/
│   ├── agents/
│   ├── tools/
│   ├── parsers/
│   ├── storage/
│   └── reports/
├── data/
│   ├── spectremind.db
│   └── sessions/
├── tests/
├── docs/
├── requirements.txt
└── README.md
Implemented Components
AETHER

Handles task classification, planning, and operational routing.

SCRIBE

Builds structured markdown reports from parsed findings and session events.

Tool Layer

Currently includes an Nmap wrapper for controlled reconnaissance.

Parser Layer

Extracts structured findings such as:

host
host status
filtered summary
open ports
services
port details
OS hints
Storage Layer

Uses SQLite for persistent storage of:

sessions
tasks
tool runs
findings
Session Artifacts

Each session stores:

session.json
report.md
nmap_stdout.txt
nmap_stderr.txt
events.jsonl
Example Commands

Initialize a session:

python -m app.main init --name vm-test

Run a scan:

python -m app.main run --objective "Scan my lab VM" --target 192.168.1.10 --approved

List sessions:

python -m app.main sessions

Show findings from latest session:

python -m app.main findings --latest

Show report:

python -m app.main report --latest

Use natural language interface:

python -m app.main ask "scan 192.168.1.10"
Design Principles
Local-first
Operator-controlled
Explicit scope validation
Full command visibility
Session traceability
Modular agent and wrapper design
Extensible architecture for future memory, routing, and multi-agent behavior
Current Status

SpectreMind is in active development.

The current milestone delivers a working vertical slice:

task in
plan created
tool executed
output parsed
findings stored
report generated

This is the foundation for future expansion into:

selective memory retrieval
multi-agent routing
broader tool integration
voice assistant workflows
proactive suggestions
Disclaimer

SpectreMind is being built for authorized security research, lab environments, and defensive learning. It is intended to remain controlled, inspectable, and operator-driven.