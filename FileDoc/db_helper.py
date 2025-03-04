import sqlite3
from datetime import datetime
import os

class AnalyticsDB:
    def __init__(self, db_path=None):
        # Use environment variable or default to local path
        self.db_path = db_path or os.getenv('DB_PATH', 'analytics.db')
        
        # Only create directories if path contains directories
        db_dir = os.path.dirname(self.db_path)
        if db_dir:  # Only try to create directory if there's a path component
            os.makedirs(db_dir, exist_ok=True)
            
        self.init_db()
    
    def init_db(self):
        """Initialize the database with required tables."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS file_operations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_file TEXT NOT NULL,
                    operation_type TEXT NOT NULL,
                    timestamp DATETIME NOT NULL,
                    file_size INTEGER NOT NULL,
                    token_count INTEGER NOT NULL,
                    estimated_cost REAL NOT NULL,
                    user_feedback TEXT,
                    was_edited BOOLEAN NOT NULL
                )
            """)
            conn.commit()
    
    def log_operation(self, source_file: str, file_size: int, token_count: int, 
                     estimated_cost: float, user_feedback: str = None):
        """Log a file documentation operation."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO file_operations 
                (source_file, operation_type, timestamp, file_size, token_count, 
                 estimated_cost, user_feedback, was_edited)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                source_file,
                'FileDoc',
                datetime.utcnow().isoformat(),
                file_size,
                token_count,
                estimated_cost,
                user_feedback,
                bool(user_feedback and user_feedback.strip())
            ))
            conn.commit() 