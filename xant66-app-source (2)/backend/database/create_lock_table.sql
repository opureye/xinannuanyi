-- 创建锁表，用于管理账号审核功能的并发访问
CREATE TABLE IF NOT EXISTS audit_locks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lock_name TEXT UNIQUE NOT NULL, -- 锁名称，用于标识不同的锁定资源
    locked_by TEXT NOT NULL, -- 锁定者的用户名
    locked_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, -- 锁定时间
    expires_at DATETIME NOT NULL, -- 锁过期时间
    lock_status TEXT NOT NULL DEFAULT 'active' -- 锁状态：active, expired
);

-- 创建索引，提高查询性能
CREATE INDEX IF NOT EXISTS idx_audit_locks_lock_name ON audit_locks(lock_name);
CREATE INDEX IF NOT EXISTS idx_audit_locks_expires_at ON audit_locks(expires_at);
CREATE INDEX IF NOT EXISTS idx_audit_locks_lock_status ON audit_locks(lock_status);
