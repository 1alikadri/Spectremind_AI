CREATE_SESSIONS_TABLE = """
CREATE TABLE IF NOT EXISTS sessions (
    session_id TEXT PRIMARY KEY,
    name TEXT,
    created_at TEXT NOT NULL,
    status TEXT NOT NULL
);
"""

CREATE_TASKS_TABLE = """
CREATE TABLE IF NOT EXISTS tasks (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    objective TEXT NOT NULL,
    target TEXT,
    category TEXT NOT NULL,
    approved INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(session_id) REFERENCES sessions(session_id)
);
"""

CREATE_TOOL_RUNS_TABLE = """
CREATE TABLE IF NOT EXISTS tool_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    tool_name TEXT NOT NULL,
    command_preview TEXT NOT NULL,
    stdout_path TEXT,
    stderr_path TEXT,
    returncode INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(session_id) REFERENCES sessions(session_id)
);
"""

CREATE_FINDINGS_TABLE = """
CREATE TABLE IF NOT EXISTS findings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    task_id TEXT,
    tool_run_id INTEGER,
    host TEXT,
    port INTEGER,
    protocol TEXT,
    state TEXT,
    service TEXT,
    version TEXT,
    os_hint TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY(session_id) REFERENCES sessions(session_id),
    FOREIGN KEY(task_id) REFERENCES tasks(id),
    FOREIGN KEY(tool_run_id) REFERENCES tool_runs(id)
);
"""

CREATE_SESSION_MEMORY_TABLE = """
CREATE TABLE IF NOT EXISTS session_memory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    summary TEXT NOT NULL,
    observations TEXT NOT NULL,
    unresolved TEXT NOT NULL,
    suggestions TEXT NOT NULL,
    tags TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(session_id) REFERENCES sessions(session_id)
);
"""
CREATE_CHAT_MESSAGES_TABLE = """
CREATE TABLE IF NOT EXISTS chat_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    metadata TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY(session_id) REFERENCES sessions(session_id)
);
"""

CREATE_SESSION_STATE_TABLE = """
CREATE TABLE IF NOT EXISTS session_state (
    session_id TEXT PRIMARY KEY,
    current_target TEXT,
    current_objective TEXT,
    active_hypotheses TEXT NOT NULL,
    unresolved_items TEXT NOT NULL,
    tool_state TEXT NOT NULL,
    next_steps TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(session_id) REFERENCES sessions(session_id)
);
"""

CREATE_LONG_TERM_MEMORIES_TABLE = """
CREATE TABLE IF NOT EXISTS long_term_memories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    memory_type TEXT NOT NULL,
    memory_key TEXT,
    content TEXT NOT NULL,
    tags TEXT NOT NULL,
    source_session_id TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(source_session_id) REFERENCES sessions(session_id)
);
"""
