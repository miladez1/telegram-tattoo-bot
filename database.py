# -*- coding: utf-8 -*-

import sqlite3
import logging
from datetime import datetime, timedelta
from config import DATABASE_NAME, PERSIAN_TEXTS

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.db_name = DATABASE_NAME
        self.init_database()

    def init_database(self):
        """Initialize database with required tables"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                first_name TEXT,
                username TEXT,
                join_date DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Slots table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS slots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                slot_text TEXT NOT NULL,
                is_available BOOLEAN DEFAULT 1
            )
        ''')
        
        # Reservations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reservations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                slot_id INTEGER,
                status TEXT DEFAULT 'pending',
                receipt_photo_id TEXT,
                pending_time DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (slot_id) REFERENCES slots(id)
            )
        ''')
        
        # Settings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')
        
        # Initialize default settings
        self.init_default_settings(cursor)
        
        conn.commit()
        conn.close()

    def init_default_settings(self, cursor):
        """Initialize default settings"""
        default_settings = {
            'welcome_message': PERSIAN_TEXTS['welcome_message'],
            'card_number': PERSIAN_TEXTS['card_number'],
            'card_owner': PERSIAN_TEXTS['card_owner'],
            'deposit_amount': PERSIAN_TEXTS['deposit_amount'],
            'force_join_channel': '',
            'ai_api_key': '',
            'contact_info': PERSIAN_TEXTS['contact_info']
        }
        
        for key, value in default_settings.items():
            cursor.execute('INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)', (key, value))

    def add_user(self, user_id, first_name, username):
        """Add or update user"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO users (user_id, first_name, username)
            VALUES (?, ?, ?)
        ''', (user_id, first_name, username))
        
        conn.commit()
        conn.close()

    def get_available_slots(self):
        """Get all available appointment slots"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('SELECT id, slot_text FROM slots WHERE is_available = 1')
        slots = cursor.fetchall()
        
        conn.close()
        return slots

    def add_slot(self, slot_text):
        """Add new appointment slot"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('INSERT INTO slots (slot_text) VALUES (?)', (slot_text,))
        
        conn.commit()
        conn.close()

    def delete_slot(self, slot_id):
        """Delete appointment slot"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM slots WHERE id = ?', (slot_id,))
        
        conn.commit()
        conn.close()

    def create_reservation(self, user_id, slot_id):
        """Create temporary reservation"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        pending_time = datetime.now()
        
        cursor.execute('''
            INSERT INTO reservations (user_id, slot_id, status, pending_time)
            VALUES (?, ?, 'pending', ?)
        ''', (user_id, slot_id, pending_time))
        
        # Make slot unavailable
        cursor.execute('UPDATE slots SET is_available = 0 WHERE id = ?', (slot_id,))
        
        reservation_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return reservation_id

    def update_reservation_receipt(self, reservation_id, receipt_photo_id):
        """Update reservation with receipt photo"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE reservations 
            SET receipt_photo_id = ? 
            WHERE id = ?
        ''', (receipt_photo_id, reservation_id))
        
        conn.commit()
        conn.close()

    def confirm_reservation(self, reservation_id):
        """Confirm reservation by admin"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE reservations 
            SET status = 'confirmed' 
            WHERE id = ?
        ''', (reservation_id,))
        
        conn.commit()
        conn.close()

    def reject_reservation(self, reservation_id):
        """Reject reservation and free the slot"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # Get slot_id before rejection
        cursor.execute('SELECT slot_id FROM reservations WHERE id = ?', (reservation_id,))
        result = cursor.fetchone()
        
        if result:
            slot_id = result[0]
            
            # Update reservation status
            cursor.execute('''
                UPDATE reservations 
                SET status = 'rejected' 
                WHERE id = ?
            ''', (reservation_id,))
            
            # Make slot available again
            cursor.execute('UPDATE slots SET is_available = 1 WHERE id = ?', (slot_id,))
        
        conn.commit()
        conn.close()

    def get_expired_reservations(self, timeout_minutes=30):
        """Get reservations that have expired"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        timeout_time = datetime.now() - timedelta(minutes=timeout_minutes)
        
        cursor.execute('''
            SELECT id, slot_id FROM reservations 
            WHERE status = 'pending' AND pending_time < ?
        ''', (timeout_time,))
        
        expired = cursor.fetchall()
        conn.close()
        
        return expired

    def cancel_expired_reservation(self, reservation_id, slot_id):
        """Cancel expired reservation and free slot"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM reservations WHERE id = ?', (reservation_id,))
        cursor.execute('UPDATE slots SET is_available = 1 WHERE id = ?', (slot_id,))
        
        conn.commit()
        conn.close()

    def get_setting(self, key):
        """Get setting value"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('SELECT value FROM settings WHERE key = ?', (key,))
        result = cursor.fetchone()
        
        conn.close()
        return result[0] if result else None

    def set_setting(self, key, value):
        """Set setting value"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)', (key, value))
        
        conn.commit()
        conn.close()

    def get_all_users(self):
        """Get all user IDs for broadcasting"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('SELECT user_id FROM users')
        users = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        return users

    def get_reservation_by_id(self, reservation_id):
        """Get reservation details by ID"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT r.*, s.slot_text, u.first_name, u.username 
            FROM reservations r
            JOIN slots s ON r.slot_id = s.id
            JOIN users u ON r.user_id = u.user_id
            WHERE r.id = ?
        ''', (reservation_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        return result