import logging
import json
from datetime import datetime
from pathlib import Path
import sqlite3
from typing import Dict, List

class SecureLogger:
    def __init__(self, log_dir="logs", db_path="logs/operations.db"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Setup file logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.log_dir / 'comms_shield.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('CommsShield')
        
        # Setup database for structured logging
        self.db_path = Path(db_path)
        self.init_database()
    
    def init_database(self):
        """Initialize SQLite database for logs"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS operation_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                level TEXT NOT NULL,
                operation TEXT NOT NULL,
                filename TEXT,
                original_size INTEGER,
                scrubbed_size INTEGER,
                metadata_removed TEXT,
                status TEXT NOT NULL,
                error_message TEXT
            )
        ''')
        conn.commit()
        conn.close()
    
    def log_operation(self, operation_data: Dict):
        """Log a scrubbing operation to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO operation_logs 
            (timestamp, level, operation, filename, original_size, scrubbed_size, metadata_removed, status, error_message)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            datetime.now().isoformat(),
            operation_data.get('level', 'INFO'),
            operation_data['operation'],
            operation_data.get('filename'),
            operation_data.get('original_size'),
            operation_data.get('scrubbed_size'),
            json.dumps(operation_data.get('metadata_removed', [])),
            operation_data['status'],
            operation_data.get('error_message')
        ))
        
        conn.commit()
        conn.close()
    
    def info(self, message, operation_data=None):
        self.logger.info(message)
        if operation_data:
            operation_data.update({'level': 'INFO', 'timestamp': datetime.now()})
            self.log_operation(operation_data)
    
    def error(self, message, operation_data=None):
        self.logger.error(message)
        if operation_data:
            operation_data.update({'level': 'ERROR', 'timestamp': datetime.now()})
            self.log_operation(operation_data)
    
    def get_recent_logs(self, limit=100):
        """Get recent logs from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM operation_logs 
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (limit,))
        logs = cursor.fetchall()
        conn.close()
        return logs
    
    def generate_report(self, days=7):
        """Generate a security report"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get stats
        cursor.execute('''
            SELECT 
                COUNT(*) as total_operations,
                SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as successful,
                SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END) as failed
            FROM operation_logs 
            WHERE timestamp > datetime('now', ?)
        ''', (f'-{days} days',))
        
        stats = cursor.fetchone()
        conn.close()
        
        return {
            'period_days': days,
            'total_operations': stats[0],
            'successful': stats[1],
            'failed': stats[2],
            'success_rate': (stats[1] / stats[0] * 100) if stats[0] > 0 else 0
        }