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
        conn = None
        try:
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
            logger.info("Database initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()

    def init_default_settings(self, cursor):
        """Initialize default settings"""
        default_settings = {
            # Basic settings
            'welcome_message': PERSIAN_TEXTS['welcome_message'],
            'card_number': PERSIAN_TEXTS['card_number'],
            'card_owner': PERSIAN_TEXTS['card_owner'],
            'deposit_amount': PERSIAN_TEXTS['deposit_amount'],
            'force_join_channel': '',
            'ai_api_key': '',
            'contact_info': PERSIAN_TEXTS['contact_info'],
            
            # Main menu button texts
            'button_ai_design': PERSIAN_TEXTS['main_menu_buttons']['ai_design'],
            'button_book_appointment': PERSIAN_TEXTS['main_menu_buttons']['book_appointment'],
            'button_contact': PERSIAN_TEXTS['main_menu_buttons']['contact'],
            'button_admin_panel': PERSIAN_TEXTS['main_menu_buttons']['admin_panel'],
            
            # AI Design messages
            'ai_design_prompt': PERSIAN_TEXTS['ai_design_prompt'],
            'ai_design_processing': PERSIAN_TEXTS['ai_design_processing'],
            'ai_design_result': PERSIAN_TEXTS['ai_design_result'],
            'ai_design_error': PERSIAN_TEXTS['ai_design_error'],
            
            # Booking messages
            'booking_select_slot': PERSIAN_TEXTS['booking_select_slot'],
            'booking_no_slots': PERSIAN_TEXTS['booking_no_slots'],
            'booking_slot_unavailable': PERSIAN_TEXTS['booking_slot_unavailable'],
            'booking_receipt_request': PERSIAN_TEXTS['booking_receipt_request'],
            'booking_receipt_received': PERSIAN_TEXTS['booking_receipt_received'],
            'booking_confirmed': PERSIAN_TEXTS['booking_confirmed'],
            'booking_rejected': PERSIAN_TEXTS['booking_rejected'],
            
            # Discount booking
            'booking_discount_select': PERSIAN_TEXTS['booking_discount_select'],
            'booking_discount_button': PERSIAN_TEXTS['booking_discount_button'],
            
            # General messages
            'back_button': PERSIAN_TEXTS['back_button'],
            'cancel_button': PERSIAN_TEXTS['cancel_button'],
            'operation_cancelled': PERSIAN_TEXTS['operation_cancelled'],
            'error_general': PERSIAN_TEXTS['error_general'],
            
            # Admin messages
            'admin_receipt_caption': PERSIAN_TEXTS['admin_receipt_caption'],
            'admin_approve_button': PERSIAN_TEXTS['admin_approve_button'],
            'admin_reject_button': PERSIAN_TEXTS['admin_reject_button']
        }
        
        for key, value in default_settings.items():
            cursor.execute('INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)', (key, value))

    def add_user(self, user_id, first_name, username):
        """Add or update user"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO users (user_id, first_name, username)
                VALUES (?, ?, ?)
            ''', (user_id, first_name, username))
            
            conn.commit()
            logger.debug(f"User {user_id} added/updated successfully")
            
        except Exception as e:
            logger.error(f"Error adding user {user_id}: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()

    def get_available_slots(self):
        """Get all available appointment slots"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            cursor.execute('SELECT id, slot_text FROM slots WHERE is_available = 1')
            slots = cursor.fetchall()
            
            return slots
            
        except Exception as e:
            logger.error(f"Error getting available slots: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def add_slot(self, slot_text):
        """Add new appointment slot"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            cursor.execute('INSERT INTO slots (slot_text) VALUES (?)', (slot_text,))
            
            conn.commit()
            logger.info(f"Slot added: {slot_text}")
            
        except Exception as e:
            logger.error(f"Error adding slot: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()

    def delete_slot(self, slot_id):
        """Delete appointment slot"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM slots WHERE id = ?', (slot_id,))
            
            conn.commit()
            logger.info(f"Slot deleted: {slot_id}")
            
        except Exception as e:
            logger.error(f"Error deleting slot {slot_id}: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()

    def create_reservation(self, user_id, slot_id):
        """Create temporary reservation"""
        conn = None
        try:
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
            
            logger.info(f"Reservation created: {reservation_id} for user {user_id}, slot {slot_id}")
            return reservation_id
            
        except Exception as e:
            logger.error(f"Error creating reservation for user {user_id}, slot {slot_id}: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()

    def update_reservation_receipt(self, reservation_id, receipt_photo_id):
        """Update reservation with receipt photo"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE reservations 
                SET receipt_photo_id = ? 
                WHERE id = ?
            ''', (receipt_photo_id, reservation_id))
            
            conn.commit()
            logger.info(f"Receipt updated for reservation {reservation_id}")
            
        except Exception as e:
            logger.error(f"Error updating receipt for reservation {reservation_id}: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()

    def confirm_reservation(self, reservation_id):
        """Confirm reservation by admin"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE reservations 
                SET status = 'confirmed' 
                WHERE id = ?
            ''', (reservation_id,))
            
            conn.commit()
            logger.info(f"Reservation confirmed: {reservation_id}")
            
        except Exception as e:
            logger.error(f"Error confirming reservation {reservation_id}: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()

    def reject_reservation(self, reservation_id):
        """Reject reservation and free the slot"""
        conn = None
        try:
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
                logger.info(f"Reservation rejected: {reservation_id}, slot {slot_id} freed")
            else:
                logger.warning(f"Reservation {reservation_id} not found for rejection")
                
        except Exception as e:
            logger.error(f"Error rejecting reservation {reservation_id}: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()

    def get_expired_reservations(self, timeout_minutes=30):
        """Get reservations that have expired"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            timeout_time = datetime.now() - timedelta(minutes=timeout_minutes)
            
            cursor.execute('''
                SELECT id, slot_id FROM reservations 
                WHERE status = 'pending' AND pending_time < ?
            ''', (timeout_time,))
            
            expired = cursor.fetchall()
            return expired
            
        except Exception as e:
            logger.error(f"Error getting expired reservations: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def cancel_expired_reservation(self, reservation_id, slot_id):
        """Cancel expired reservation and free slot"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM reservations WHERE id = ?', (reservation_id,))
            cursor.execute('UPDATE slots SET is_available = 1 WHERE id = ?', (slot_id,))
            
            conn.commit()
            logger.info(f"Expired reservation cancelled: {reservation_id}, slot {slot_id} freed")
            
        except Exception as e:
            logger.error(f"Error cancelling expired reservation {reservation_id}: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()

    def get_setting(self, key):
        """Get setting value"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            cursor.execute('SELECT value FROM settings WHERE key = ?', (key,))
            result = cursor.fetchone()
            
            return result[0] if result else None
            
        except Exception as e:
            logger.error(f"Error getting setting {key}: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def set_setting(self, key, value):
        """Set setting value"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            cursor.execute('INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)', (key, value))
            
            conn.commit()
            logger.debug(f"Setting updated: {key}")
            
        except Exception as e:
            logger.error(f"Error setting {key}: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()

    def get_all_users(self):
        """Get all user IDs for broadcasting"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            cursor.execute('SELECT user_id FROM users')
            users = [row[0] for row in cursor.fetchall()]
            
            return users
            
        except Exception as e:
            logger.error(f"Error getting all users: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def get_reservations_near_expiry(self, timeout_minutes=120, warning_minutes=30):
        """Get reservations that will expire soon (for notifications)"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            # Get reservations that will expire in warning_minutes
            warning_time = datetime.now() - timedelta(minutes=(timeout_minutes - warning_minutes))
            
            cursor.execute('''
                SELECT r.id, r.user_id, s.slot_text, r.pending_time
                FROM reservations r
                JOIN slots s ON r.slot_id = s.id
                WHERE r.status = 'pending' 
                AND r.pending_time < ?
                AND r.id NOT IN (
                    SELECT reservation_id FROM expiry_warnings WHERE reservation_id = r.id
                )
            ''', (warning_time,))
            
            near_expiry = cursor.fetchall()
            return near_expiry
            
        except Exception as e:
            logger.error(f"Error getting reservations near expiry: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def mark_expiry_warning_sent(self, reservation_id):
        """Mark that expiry warning has been sent for a reservation"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            # Create expiry_warnings table if it doesn't exist
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS expiry_warnings (
                    reservation_id INTEGER PRIMARY KEY,
                    warning_sent_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                INSERT OR IGNORE INTO expiry_warnings (reservation_id)
                VALUES (?)
            ''', (reservation_id,))
            
            conn.commit()
            
        except Exception as e:
            logger.error(f"Error marking expiry warning sent for reservation {reservation_id}: {e}")
        finally:
            if conn:
                conn.close()

    def get_reservation_by_id(self, reservation_id):
        """Get reservation details by ID"""
        conn = None
        try:
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
            return result
            
        except Exception as e:
            logger.error(f"Error getting reservation {reservation_id}: {e}")
            return None
        finally:
            if conn:
                conn.close()