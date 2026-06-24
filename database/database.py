"""
YamGuard - Database Layer
SQLite database operations with MySQL API support for future online sync
"""

import os
import sqlite3
import json
import hashlib
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from contextlib import contextmanager

from utils.constants import DB_PATH, DATABASE_DIR, UPLOADS_DIR
from utils.helpers import hash_password, get_timestamp


class DatabaseManager:
    """Central database manager for all SQLite operations"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.db_path = DB_PATH
        self._ensure_database()
    
    def _ensure_database(self):
        """Ensure database exists and schema is applied"""
        os.makedirs(DATABASE_DIR, exist_ok=True)
        if not os.path.exists(self.db_path):
            self._init_schema()
        else:
            # Ensure schema is up to date
            self._init_schema()
    
    def _init_schema(self):
        """Initialize database schema from SQL file"""
        schema_path = os.path.join(DATABASE_DIR, "schema.sql")
        if os.path.exists(schema_path):
            with open(schema_path, 'r') as f:
                schema = f.read()
            
            with self._get_connection() as conn:
                conn.executescript(schema)
    
    @contextmanager
    def _get_connection(self):
        """Get database connection with proper configuration"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def execute(self, query: str, params: tuple = ()) -> List[sqlite3.Row]:
        """Execute a query and return results"""
        with self._get_connection() as conn:
            cursor = conn.execute(query, params)
            return cursor.fetchall()
    
    def execute_one(self, query: str, params: tuple = ()) -> Optional[sqlite3.Row]:
        """Execute a query and return single result"""
        results = self.execute(query, params)
        return results[0] if results else None
    
    def execute_insert(self, query: str, params: tuple = ()) -> int:
        """Execute insert and return last row id"""
        with self._get_connection() as conn:
            cursor = conn.execute(query, params)
            return cursor.lastrowid
    
    def execute_update(self, query: str, params: tuple = ()) -> int:
        """Execute update/delete and return affected rows"""
        with self._get_connection() as conn:
            cursor = conn.execute(query, params)
            return cursor.rowcount


class UserRepository:
    """User data access layer"""
    
    def __init__(self, db: DatabaseManager = None):
        self.db = db or DatabaseManager()
    
    def create_user(self, fullname: str, email: str, password: str, 
                   role: str = "farmer", phone: str = "", 
                   organization: str = "") -> Optional[int]:
        """Create new user account"""
        try:
            hashed_password = hash_password(password)
            query = """
                INSERT INTO users (fullname, email, password, role, phone, organization)
                VALUES (?, ?, ?, ?, ?, ?)
            """
            return self.db.execute_insert(query, (fullname, email.lower(), hashed_password, role, phone, organization))
        except sqlite3.IntegrityError:
            return None
    
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email address"""
        query = "SELECT * FROM users WHERE email = ? AND is_active = 1"
        row = self.db.execute_one(query, (email.lower(),))
        return dict(row) if row else None
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        query = "SELECT * FROM users WHERE id = ?"
        row = self.db.execute_one(query, (user_id,))
        return dict(row) if row else None
    
    def authenticate_user(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user with email and password"""
        user = self.get_user_by_email(email)
        if user and hash_password(password) == user['password']:
            # Update last login
            self.db.execute_update(
                "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?",
                (user['id'],)
            )
            # Remove password from returned dict
            user.pop('password', None)
            return user
        return None
    
    def update_user(self, user_id: int, **kwargs) -> bool:
        """Update user information"""
        allowed_fields = ['fullname', 'phone', 'organization', 'profile_image', 'role']
        updates = {k: v for k, v in kwargs.items() if k in allowed_fields}
        
        if not updates:
            return False
        
        set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
        query = f"UPDATE users SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = ?"
        params = tuple(updates.values()) + (user_id,)
        
        return self.db.execute_update(query, params) > 0
    
    def change_password(self, user_id: int, new_password: str) -> bool:
        """Change user password"""
        hashed = hash_password(new_password)
        query = "UPDATE users SET password = ? WHERE id = ?"
        return self.db.execute_update(query, (hashed, user_id)) > 0
    
    def get_all_users(self) -> List[Dict[str, Any]]:
        """Get all users (admin only)"""
        query = "SELECT id, fullname, email, role, created_at, last_login, is_active FROM users ORDER BY created_at DESC"
        rows = self.db.execute(query)
        return [dict(row) for row in rows]


class ScanRepository:
    """Scan data access layer"""
    
    def __init__(self, db: DatabaseManager = None):
        self.db = db or DatabaseManager()
    
    def create_scan(self, user_id: int, tuber_id: str, image_path: str,
                    classification: str, severity_level: str,
                    confidence_score: float, recommendation: str,
                    spectral_data: dict = None, pca_data: dict = None,
                    probability_map: dict = None,
                    thumbnail_path: str = "") -> int:
        """Save new scan record"""
        query = """
            INSERT INTO scans (user_id, tuber_id, image_path, thumbnail_path,
                             classification, severity_level, confidence_score,
                             recommendation, spectral_data, pca_data, probability_map)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            user_id, tuber_id, image_path, thumbnail_path,
            classification, severity_level, confidence_score,
            recommendation,
            json.dumps(spectral_data) if spectral_data else None,
            json.dumps(pca_data) if pca_data else None,
            json.dumps(probability_map) if probability_map else None,
        )
        return self.db.execute_insert(query, params)
    
    def get_scan_by_id(self, scan_id: int) -> Optional[Dict[str, Any]]:
        """Get scan by ID"""
        query = "SELECT * FROM scans WHERE id = ?"
        row = self.db.execute_one(query, (scan_id,))
        if row:
            result = dict(row)
            # Parse JSON fields
            for field in ['spectral_data', 'pca_data', 'probability_map']:
                if result.get(field):
                    try:
                        result[field] = json.loads(result[field])
                    except (json.JSONDecodeError, TypeError):
                        result[field] = None
            return result
        return None
    
    def get_user_scans(self, user_id: int, limit: int = 50, 
                       offset: int = 0) -> List[Dict[str, Any]]:
        """Get scans for a user"""
        query = """
            SELECT * FROM scans 
            WHERE user_id = ? 
            ORDER BY scan_date DESC 
            LIMIT ? OFFSET ?
        """
        rows = self.db.execute(query, (user_id, limit, offset))
        return [self._parse_scan_row(dict(row)) for row in rows]
    
    def get_recent_scans(self, user_id: int, limit: int = 5) -> List[Dict[str, Any]]:
        """Get recent scans for dashboard"""
        query = """
            SELECT id, tuber_id, classification, severity_level, 
                   confidence_score, scan_date
            FROM scans 
            WHERE user_id = ? 
            ORDER BY scan_date DESC 
            LIMIT ?
        """
        rows = self.db.execute(query, (user_id, limit))
        return [dict(row) for row in rows]
    
    def search_scans(self, user_id: int, search: str = "", 
                     date_from: str = "", date_to: str = "",
                     status_filter: str = "") -> List[Dict[str, Any]]:
        """Search and filter scans"""
        query = "SELECT * FROM scans WHERE user_id = ?"
        params = [user_id]
        
        if search:
            query += " AND (tuber_id LIKE ? OR classification LIKE ?)"
            params.extend([f"%{search}%", f"%{search}%"])
        
        if date_from:
            query += " AND date(scan_date) >= date(?)"
            params.append(date_from)
        
        if date_to:
            query += " AND date(scan_date) <= date(?)"
            params.append(date_to)
        
        if status_filter:
            if status_filter.lower() == "healthy":
                query += " AND classification = 'Healthy'"
            elif status_filter.lower() == "infected":
                query += " AND classification != 'Healthy'"
        
        query += " ORDER BY scan_date DESC"
        
        rows = self.db.execute(query, tuple(params))
        return [self._parse_scan_row(dict(row)) for row in rows]
    
    def get_scan_statistics(self, user_id: int) -> Dict[str, Any]:
        """Get scan statistics for dashboard"""
        # Total scans
        total = self.db.execute_one(
            "SELECT COUNT(*) as count FROM scans WHERE user_id = ?",
            (user_id,)
        )
        total_count = total['count'] if total else 0
        
        # Healthy count
        healthy = self.db.execute_one(
            "SELECT COUNT(*) as count FROM scans WHERE user_id = ? AND classification = 'Healthy'",
            (user_id,)
        )
        healthy_count = healthy['count'] if healthy else 0
        
        # Infected count
        infected_count = total_count - healthy_count
        
        # Infection rate
        infection_rate = round((infected_count / total_count) * 100, 1) if total_count > 0 else 0.0
        
        return {
            "total_scans": total_count,
            "healthy_count": healthy_count,
            "infected_count": infected_count,
            "infection_rate": infection_rate,
        }
    
    def delete_scan(self, scan_id: int, user_id: int) -> bool:
        """Delete a scan record"""
        query = "DELETE FROM scans WHERE id = ? AND user_id = ?"
        return self.db.execute_update(query, (scan_id, user_id)) > 0
    
    def _parse_scan_row(self, row: dict) -> dict:
        """Parse scan row with JSON fields"""
        for field in ['spectral_data', 'pca_data', 'probability_map']:
            if row.get(field):
                try:
                    row[field] = json.loads(row[field])
                except (json.JSONDecodeError, TypeError):
                    row[field] = None
        return row


class ReportRepository:
    """Report data access layer"""
    
    def __init__(self, db: DatabaseManager = None):
        self.db = db or DatabaseManager()
    
    def create_report(self, user_id: int, report_title: str,
                      date_from: str = "", date_to: str = "",
                      classification_filter: str = "",
                      total_scans: int = 0, healthy_count: int = 0,
                      infected_count: int = 0, infection_rate: float = 0.0,
                      comments: str = "", pdf_file: str = "") -> int:
        """Save report record"""
        query = """
            INSERT INTO reports (user_id, report_title, date_from, date_to,
                               classification_filter, total_scans, healthy_count,
                               infected_count, infection_rate, comments, pdf_file)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (user_id, report_title, date_from, date_to,
                 classification_filter, total_scans, healthy_count,
                 infected_count, infection_rate, comments, pdf_file)
        return self.db.execute_insert(query, params)
    
    def get_user_reports(self, user_id: int) -> List[Dict[str, Any]]:
        """Get reports for a user"""
        query = """
            SELECT id, report_title, date_from, date_to,
                   total_scans, healthy_count, infected_count,
                   infection_rate, pdf_file, created_at
            FROM reports 
            WHERE user_id = ? 
            ORDER BY created_at DESC
        """
        rows = self.db.execute(query, (user_id,))
        return [dict(row) for row in rows]
    
    def get_report_by_id(self, report_id: int) -> Optional[Dict[str, Any]]:
        """Get report by ID"""
        query = "SELECT * FROM reports WHERE id = ?"
        row = self.db.execute_one(query, (report_id,))
        return dict(row) if row else None


class SettingsRepository:
    """Settings data access layer"""
    
    def __init__(self, db: DatabaseManager = None):
        self.db = db or DatabaseManager()
    
    def get_setting(self, user_id: int, key: str, default: str = "") -> str:
        """Get setting value"""
        query = "SELECT setting_value FROM settings WHERE user_id = ? AND setting_key = ?"
        row = self.db.execute_one(query, (user_id, key))
        return row['setting_value'] if row else default
    
    def set_setting(self, user_id: int, key: str, value: str):
        """Set or update setting"""
        query = """
            INSERT INTO settings (user_id, setting_key, setting_value)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id, setting_key) 
            DO UPDATE SET setting_value = excluded.setting_value
        """
        self.db.execute_update(query, (user_id, key, value))


class ActivityLogRepository:
    """Activity logging"""
    
    def __init__(self, db: DatabaseManager = None):
        self.db = db or DatabaseManager()
    
    def log_activity(self, user_id: int, action: str, details: str = ""):
        """Log user activity"""
        query = "INSERT INTO activity_log (user_id, action, details) VALUES (?, ?, ?)"
        self.db.execute_insert(query, (user_id, action, details))
    
    def get_recent_activities(self, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent activities"""
        query = """
            SELECT action, details, created_at 
            FROM activity_log 
            WHERE user_id = ? 
            ORDER BY created_at DESC 
            LIMIT ?
        """
        rows = self.db.execute(query, (user_id, limit))
        return [dict(row) for row in rows]


# Global database instance
db = DatabaseManager()
user_repo = UserRepository(db)
scan_repo = ScanRepository(db)
report_repo = ReportRepository(db)
settings_repo = SettingsRepository(db)
activity_repo = ActivityLogRepository(db)
