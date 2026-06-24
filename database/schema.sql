-- YamGuard Database Schema
-- SQLite database for offline mode with MySQL API support for future online sync

-- Enable foreign keys
PRAGMA foreign_keys = ON;

-- Users table: Store user accounts and authentication
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fullname TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role TEXT DEFAULT 'farmer',
    phone TEXT,
    organization TEXT,
    profile_image TEXT,
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

-- Create index on email for faster lookups
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- Scans table: Store tuber scan records
CREATE TABLE IF NOT EXISTS scans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    tuber_id TEXT UNIQUE NOT NULL,
    image_path TEXT NOT NULL,
    thumbnail_path TEXT,
    classification TEXT NOT NULL,
    severity_level TEXT NOT NULL,
    confidence_score REAL NOT NULL,
    recommendation TEXT,
    spectral_data TEXT,
    pca_data TEXT,
    probability_map TEXT,
    scan_location TEXT,
    scan_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sync_status INTEGER DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Create indexes for scans
CREATE INDEX IF NOT EXISTS idx_scans_user_id ON scans(user_id);
CREATE INDEX IF NOT EXISTS idx_scans_date ON scans(scan_date);
CREATE INDEX IF NOT EXISTS idx_scans_classification ON scans(classification);
CREATE INDEX IF NOT EXISTS idx_scans_tuber_id ON scans(tuber_id);

-- Reports table: Store generated PDF reports
CREATE TABLE IF NOT EXISTS reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    report_title TEXT NOT NULL,
    date_from TEXT,
    date_to TEXT,
    classification_filter TEXT,
    total_scans INTEGER DEFAULT 0,
    healthy_count INTEGER DEFAULT 0,
    infected_count INTEGER DEFAULT 0,
    infection_rate REAL DEFAULT 0.0,
    comments TEXT,
    pdf_file TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Create index for reports
CREATE INDEX IF NOT EXISTS idx_reports_user_id ON reports(user_id);

-- Spectral reference table: Store reference spectral signatures
CREATE TABLE IF NOT EXISTS spectral_references (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    reference_name TEXT NOT NULL,
    reference_type TEXT NOT NULL,
    wavelengths TEXT NOT NULL,
    reflectance_values TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Settings table: Store user preferences and app settings
CREATE TABLE IF NOT EXISTS settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    setting_key TEXT NOT NULL,
    setting_value TEXT,
    UNIQUE(user_id, setting_key),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Activity log table: Track user actions
CREATE TABLE IF NOT EXISTS activity_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    action TEXT NOT NULL,
    details TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

-- Insert default spectral reference (healthy yam signature)
INSERT OR IGNORE INTO spectral_references (id, reference_name, reference_type, wavelengths, reflectance_values)
VALUES (1, 'Healthy Yam Reference', 'baseline', '[]', '[]');

-- Insert default admin user (password: admin123 - hashed)
-- Note: In production, use proper bcrypt hashing
INSERT OR IGNORE INTO users (id, fullname, email, password, role)
VALUES (1, 'System Administrator', 'admin@yamguard.com', '5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8', 'admin');
