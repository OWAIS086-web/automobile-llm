import os
import sqlite3
import threading
from flask import current_app

# Thread-local storage for database connections
local_storage = threading.local()

# Database configuration
DATA_DIR = "data"
DB_PATH = os.path.join(DATA_DIR, "posts.db")

def get_db_connection():
    """Get fresh database connection"""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize main application database with all necessary tables"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # Users table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        company_id TEXT DEFAULT 'haval',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_login TIMESTAMP,
        is_active BOOLEAN DEFAULT TRUE
    )
    """)
    
    # Add company_id column to existing users table if it doesn't exist
    try:
        cur.execute("ALTER TABLE users ADD COLUMN company_id TEXT DEFAULT 'haval'")
        print("[DB] Added company_id column to users table")
    except sqlite3.OperationalError:
        # Column already exists
        pass
    
    # Sessions table for better session management
    cur.execute("""
    CREATE TABLE IF NOT EXISTS user_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        session_token TEXT UNIQUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        expires_at TIMESTAMP,
        is_active BOOLEAN DEFAULT TRUE,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    """)
    
    # Posts table (user-specific data)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        category TEXT,
        topic_title TEXT,
        topic_url TEXT,
        post_number INTEGER,
        author TEXT,
        created_at TEXT,
        cooked_text TEXT,
        scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    """)
    
    # Search results table (user-specific data)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS search_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        search_query TEXT,
        topic_title TEXT,
        topic_url TEXT,
        post_number INTEGER,
        author TEXT,
        created_at TEXT,
        post_text TEXT,
        scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    """)
    
    # WhatsApp messages table (shared data - no user_id needed)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS whatsapp_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_name TEXT,
        country_code INTEGER,
        contact_number INTEGER,
        message_type TEXT,
        message TEXT,
        timestamp TEXT,
        imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        sender TEXT DEFAULT 'customer',
        company_id TEXT DEFAULT 'haval'
    )
    """)
    
    # Migration: Add company_id column to whatsapp_messages if it doesn't exist
    try:
        cur.execute("ALTER TABLE whatsapp_messages ADD COLUMN company_id TEXT DEFAULT 'haval'")
        print("✅ Added company_id column to whatsapp_messages table")
    except sqlite3.OperationalError:
        # Column already exists
        pass

    # Migration: Add sender column if it doesn't exist
    try:
        cur.execute("ALTER TABLE whatsapp_messages ADD COLUMN sender TEXT DEFAULT 'customer'")
        print("✅ Added sender column to whatsapp_messages table")
    except sqlite3.OperationalError:
        # Column already exists
        pass
    
    # Chat history table (user-specific)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS chat_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        session_id TEXT,
        mode TEXT DEFAULT 'pakwheels',
        query TEXT,
        response TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    """)
    
    # Issues tables (shared data - no user_id needed)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS issues (
        id INTEGER PRIMARY KEY,
        platform_reference TEXT,
        issue_type TEXT,
        exact_issue_description TEXT,
        severity_estimate TEXT,
        first_seen_public_example TEXT,
        recommended_action TEXT,
        imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    cur.execute("""
    CREATE TABLE IF NOT EXISTS facebook_issues (
        id INTEGER PRIMARY KEY,
        platform_reference TEXT,
        issue_type TEXT,
        exact_issue_description TEXT,
        severity_estimate TEXT,
        first_seen_public_example TEXT,
        user_name TEXT,
        reference_link TEXT,
        recommended_action TEXT,
        imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # System settings table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS system_settings (
        key TEXT PRIMARY KEY,
        value TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Migration: Add post_number column if it doesn't exist
    try:
        cur.execute("SELECT post_number FROM posts LIMIT 1")
    except sqlite3.OperationalError:
        print("Adding missing post_number column to posts table...")
        cur.execute("ALTER TABLE posts ADD COLUMN post_number INTEGER")
        print("✅ Added post_number column")

    # Migration: Add company_id column if it doesn't exist
    try:
        cur.execute("SELECT company_id FROM posts LIMIT 1")
    except sqlite3.OperationalError:
        print("Adding missing company_id column to posts table...")
        cur.execute("ALTER TABLE posts ADD COLUMN company_id TEXT DEFAULT 'haval'")
        print("✅ Added company_id column to posts table")

    try:
        cur.execute("SELECT company_id FROM search_results LIMIT 1")
    except sqlite3.OperationalError:
        print("Adding missing company_id column to search_results table...")
        cur.execute("ALTER TABLE search_results ADD COLUMN company_id TEXT DEFAULT 'haval'")
        print("✅ Added company_id column to search_results table")

    conn.commit()
    conn.close()

def get_user_data_dir(user_id):
    """Get user-specific data directory"""
    user_data_dir = os.path.join(DATA_DIR, f"user_{user_id}")
    os.makedirs(user_data_dir, exist_ok=True)
    return user_data_dir