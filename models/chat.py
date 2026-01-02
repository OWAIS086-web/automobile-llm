from .database import get_db_connection
from utils.logger import database_logger, chat_logger, log_function_call, log_database_activity, log_error


@log_function_call(chat_logger)
def get_user_chat_history(user_id, mode, session_id=None, limit=50):
    """Get user-specific chat history for a mode"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        if session_id:
            cur.execute("""
                SELECT query, response FROM chat_history 
                WHERE user_id = ? AND mode = ? AND session_id = ?
                ORDER BY timestamp ASC LIMIT ?
            """, (user_id, mode, session_id, limit))
            chat_logger.info(f"Retrieved chat history for user {user_id}, mode {mode}, session {session_id}")
        else:
            cur.execute("""
                SELECT query, response FROM chat_history 
                WHERE user_id = ? AND mode = ?
                ORDER BY timestamp DESC LIMIT ?
            """, (user_id, mode, limit))
            chat_logger.info(f"Retrieved chat history for user {user_id}, mode {mode}")
        
        rows = cur.fetchall()
        history = []
        
        for row in rows:
            history.append({"role": "user", "content": row[0]})
            history.append({"role": "assistant", "content": row[1]})
        
        conn.close()
        log_database_activity("SELECT", "chat_history", len(rows), user_id)
        return history
        
    except Exception as e:
        log_error(e, f"Failed to get chat history for user {user_id}")
        return []


@log_function_call(chat_logger, log_args=False)  # Don't log full query/response content
def save_user_chat_history(user_id, session_id, mode, query, response):
    """Save user chat interaction to database"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            INSERT INTO chat_history (user_id, session_id, mode, query, response)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, session_id, mode, query, response))
        
        conn.commit()
        conn.close()
        
        chat_logger.info(f"Saved chat interaction for user {user_id}, session {session_id}, mode {mode}")
        log_database_activity("INSERT", "chat_history", 1, user_id)
        
    except Exception as e:
        log_error(e, f"Failed to save chat history for user {user_id}")


@log_function_call(chat_logger)
def get_user_chat_sessions(user_id, limit=20):
    """Get user's recent chat sessions"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT DISTINCT session_id, mode, 
                   MIN(timestamp) as first_message,
                   MAX(timestamp) as last_activity,
                   COUNT(*) / 2 as message_count,
                   MIN(query) as first_query
            FROM chat_history 
            WHERE user_id = ?
            GROUP BY session_id, mode
            ORDER BY last_activity DESC
            LIMIT ?
        """, (user_id, limit))
        
        sessions = [dict(row) for row in cur.fetchall()]
        conn.close()
        
        chat_logger.info(f"Retrieved {len(sessions)} chat sessions for user {user_id}")
        log_database_activity("SELECT", "chat_history", len(sessions), user_id)
        return sessions
        
    except Exception as e:
        log_error(e, f"Failed to get chat sessions for user {user_id}")
        return []


@log_function_call(chat_logger)
def delete_user_chat_session(user_id, session_id):
    """Delete a specific chat session for a user"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            DELETE FROM chat_history 
            WHERE user_id = ? AND session_id = ?
        """, (user_id, session_id))
        
        conn.commit()
        result = cur.rowcount > 0
        conn.close()
        
        if result:
            chat_logger.info(f"Deleted chat session {session_id} for user {user_id}")
            log_database_activity("DELETE", "chat_history", cur.rowcount, user_id)
        else:
            chat_logger.warning(f"No chat session found to delete: {session_id} for user {user_id}")
            
        return result
        
    except Exception as e:
        log_error(e, f"Failed to delete chat session {session_id} for user {user_id}")
        return False


@log_function_call(chat_logger)
def clear_user_chat_history(user_id, mode=None):
    """Clear all chat history for a user (optionally for a specific mode)"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        if mode:
            cur.execute("""
                DELETE FROM chat_history 
                WHERE user_id = ? AND mode = ?
            """, (user_id, mode))
            chat_logger.info(f"Cleared chat history for user {user_id}, mode {mode}")
        else:
            cur.execute("""
                DELETE FROM chat_history 
                WHERE user_id = ?
            """, (user_id,))
            chat_logger.info(f"Cleared all chat history for user {user_id}")
        
        conn.commit()
        result = cur.rowcount > 0
        conn.close()
        
        log_database_activity("DELETE", "chat_history", cur.rowcount, user_id)
        return result
        
    except Exception as e:
        log_error(e, f"Failed to clear chat history for user {user_id}")
        return False