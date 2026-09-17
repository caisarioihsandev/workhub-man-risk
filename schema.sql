CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    full_name TEXT NOT NULL,
    email TEXT NOT NULL DEFAULT '',
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'user' CHECK (role IN ('superadmin', 'user', 'vice_president')),
    is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS
idx_users_username
ON users(username);

CREATE INDEX IF NOT EXISTS
idx_users_role
ON users(role);

CREATE TABLE IF NOT EXISTS work_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    category TEXT NOT NULL,
    pic TEXT NOT NULL DEFAULT '',
    assignees TEXT NOT NULL DEFAULT '',
    priority TEXT NOT NULL DEFAULT 'Sedang',
    status TEXT NOT NULL DEFAULT 'Belum Dimulai',
    progress INTEGER NOT NULL DEFAULT 0 CHECK(progress BETWEEN 0 AND 100),
    deadline TEXT NOT NULL DEFAULT '',
    drive_url TEXT NOT NULL DEFAULT '',
    notes TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS
idx_work_items_status
ON work_items(status);

CREATE INDEX IF NOT EXISTS
idx_work_items_category
ON work_items(category);

CREATE INDEX IF NOT EXISTS
idx_work_items_deadline
ON work_items(deadline);

-- ============================================================
-- DATABASE DOKUMEN
-- ============================================================

CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    document_type TEXT NOT NULL DEFAULT '',
    drive_url TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_documents_type
ON documents(document_type);