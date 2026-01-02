from flask import jsonify, request
from flask_login import current_user, login_required
from models.chat import (
    get_user_chat_sessions, get_user_chat_history, 
    delete_user_chat_session, clear_user_chat_history,
    save_user_chat_history
)
from models.database import get_db_connection
from utils.logger import api_logger, log_function_call, log_user_action, log_error
import secrets
import json
import queue


@log_function_call(api_logger)
def get_selected_company():
    """Get the user's company"""
    api_logger.info(f"API: Get selected company for user {current_user.username}")
    
    from config import get_company_config
    try:
        company_config = get_company_config(current_user.company_id)
        
        response_data = {
            "success": True,
            "company": {
                "id": current_user.company_id,
                "name": company_config.full_name,
                "display_name": company_config.name  # Fix: use name instead of display_name
            }
        }
        
        api_logger.info(f"API: Company data returned for {current_user.username}: {current_user.company_id}")
        log_user_action("API: Get Company", current_user.id, f"Company: {current_user.company_id}")
        
        return jsonify(response_data)
        
    except Exception as e:
        log_error(e, f"API: Get selected company failed for user {current_user.username}")
        
        response_data = {
            "success": False,
            "error": str(e),
            "company": {
                "id": current_user.company_id,
                "name": current_user.company_id.title(),
                "display_name": current_user.company_id.title()  # This one is correct
            }
        }
        
        api_logger.error(f"API: Error getting company for {current_user.username}: {str(e)}")
        return jsonify(response_data)


@log_function_call(api_logger)
def set_selected_company():
    """This endpoint is deprecated - company is now set during user registration"""
    api_logger.warning(f"API: Deprecated set_selected_company called by user {current_user.username}")
    log_user_action("API: Set Company (Deprecated)", current_user.id, "Attempted to use deprecated endpoint")
    
    return jsonify({
        "success": False,
        "message": "Company selection is now handled during registration. Please contact support to change your company."
    })


@log_function_call(api_logger)
def get_all_companies_api():
    """Get list of all available companies"""
    api_logger.info(f"API: Get all companies requested by user {current_user.username}")
    
    from config import get_enabled_companies
    try:
        companies = get_enabled_companies()
        
        response_data = {
            "success": True,
            "companies": [
                {"id": company_id, "name": company_data}
                for company_id, company_data in companies.items()
            ]
        }
        
        api_logger.info(f"API: Returned {len(companies)} companies to user {current_user.username}")
        log_user_action("API: Get All Companies", current_user.id, f"Companies: {len(companies)}")
        
        return jsonify(response_data)
        
    except Exception as e:
        log_error(e, f"API: Get all companies failed for user {current_user.username}")
        
        fallback_companies = [
            {"id": "haval", "name": "Haval"},
            {"id": "mg", "name": "MG"},
            {"id": "kia", "name": "Kia"}
        ]
        
        api_logger.error(f"API: Using fallback companies for {current_user.username}: {str(e)}")
        
        return jsonify({
            "success": False,
            "error": str(e),
            "companies": fallback_companies
        })


@log_function_call(api_logger)
def get_chat_sessions():
    """Get user's chat sessions"""
    api_logger.info(f"API: Get chat sessions for user {current_user.username}")
    
    try:
        sessions = get_user_chat_sessions(current_user.id)
        
        api_logger.info(f"API: Retrieved {len(sessions)} chat sessions for user {current_user.username}")
        log_user_action("API: Get Chat Sessions", current_user.id, f"Sessions: {len(sessions)}")
        
        return jsonify({"success": True, "sessions": sessions})
        
    except Exception as e:
        log_error(e, f"API: Get chat sessions failed for user {current_user.username}")
        api_logger.error(f"API: Error getting chat sessions for {current_user.username}: {str(e)}")
        
        return jsonify({"success": False, "error": str(e)})


@log_function_call(api_logger)
def get_session_history(session_id):
    """Get chat history for a specific session"""
    api_logger.info(f"API: Get session history for user {current_user.username}, session {session_id}")
    
    try:
        # Get mode from query parameter, default to pakwheels for backward compatibility
        mode = request.args.get('mode', 'pakwheels')
        
        history = get_user_chat_history(current_user.id, mode, session_id)
        
        api_logger.info(f"API: Retrieved {len(history)} messages for session {session_id}, user {current_user.username}, mode {mode}")
        log_user_action("API: Get Session History", current_user.id, f"Session: {session_id}, Mode: {mode}, Messages: {len(history)}")
        
        return jsonify({"success": True, "history": history})
        
    except Exception as e:
        log_error(e, f"API: Get session history failed for user {current_user.username}, session {session_id}")
        api_logger.error(f"API: Error getting session history for {current_user.username}: {str(e)}")
        
        return jsonify({"success": False, "error": str(e)})


@log_function_call(api_logger)
def delete_chat_session(session_id):
    """Delete a chat session"""
    api_logger.info(f"API: Delete chat session {session_id} for user {current_user.username}")
    
    try:
        success = delete_user_chat_session(current_user.id, session_id)
        
        if success:
            api_logger.info(f"API: Successfully deleted session {session_id} for user {current_user.username}")
            log_user_action("API: Delete Chat Session", current_user.id, f"Session: {session_id}")
            
            return jsonify({"success": True, "message": "Session deleted successfully"})
        else:
            api_logger.warning(f"API: Session {session_id} not found for user {current_user.username}")
            return jsonify({"success": False, "error": "Session not found"})
            
    except Exception as e:
        log_error(e, f"API: Delete chat session failed for user {current_user.username}, session {session_id}")
        api_logger.error(f"API: Error deleting session for {current_user.username}: {str(e)}")
        
        return jsonify({"success": False, "error": str(e)})


@log_function_call(api_logger)
def clear_chat_history():
    """Clear user's chat history"""
    api_logger.info(f"API: Clear chat history for user {current_user.username}")
    
    try:
        mode = request.json.get('mode') if request.json else None
        success = clear_user_chat_history(current_user.id, mode)
        
        if success:
            message = f"Chat history cleared for {mode} mode" if mode else "All chat history cleared"
            
            api_logger.info(f"API: {message} for user {current_user.username}")
            log_user_action("API: Clear Chat History", current_user.id, f"Mode: {mode or 'all'}")
            
            return jsonify({"success": True, "message": message})
        else:
            api_logger.info(f"API: No chat history to clear for user {current_user.username}")
            return jsonify({"success": False, "error": "No chat history found to clear"})
            
    except Exception as e:
        log_error(e, f"API: Clear chat history failed for user {current_user.username}")
        api_logger.error(f"API: Error clearing chat history for {current_user.username}: {str(e)}")
        
        return jsonify({"success": False, "error": str(e)})


@log_function_call(api_logger)
def api_pipeline_status():
    """Get current pipeline status for status indicator"""
    # Handle both authenticated and anonymous users
    username = current_user.username if current_user.is_authenticated else "anonymous"
    user_id = current_user.id if current_user.is_authenticated else None
    
    api_logger.info(f"API: Pipeline status requested by user {username}")
    
    try:
        from ai.haval_pipeline import get_pipeline_status
        status = get_pipeline_status()
        
        api_logger.info(f"API: Pipeline status returned: {status.get('status', 'unknown')} for user {username}")
        
        # Only log user action if user is authenticated
        if current_user.is_authenticated:
            log_user_action("API: Pipeline Status", user_id, f"Status: {status.get('status', 'unknown')}")
        
        return jsonify(status)
        
    except Exception as e:
        username = current_user.username if current_user.is_authenticated else "anonymous"
        log_error(e, f"API: Pipeline status failed for user {username}")
        api_logger.error(f"API: Error getting pipeline status for {username}: {str(e)}")
        
        return jsonify({"status": "error", "message": str(e)})


@log_function_call(api_logger)
def get_wati_progress():
    """Get current WATI fetching progress"""
    if not current_user.is_authenticated:
        return jsonify({"error": "Authentication required"}), 401
    
    # Check if user has access to WATI data (only Haval users)
    user_company = current_user.company_id or 'haval'
    if user_company != 'haval':
        return jsonify({"error": "WATI access restricted to Haval users"}), 403
    
    try:
        # This is a simple implementation - in a real scenario, you'd track progress in a database or cache
        # For now, we'll return a simulated progress or check if WATI process is running
        
        # Check if there are recent WATI logs to determine if process is running
        import os
        from datetime import datetime, timedelta
        
        log_file = "logs/fetching.log"
        if os.path.exists(log_file):
            # Check if there are recent WATI-related log entries
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    
                # Look for recent processing messages
                recent_cutoff = datetime.now() - timedelta(minutes=5)
                processing_lines = []
                
                for line in reversed(lines[-100:]):  # Check last 100 lines
                    if 'Processing' in line and ('/' in line):
                        try:
                            # Extract timestamp from log line
                            timestamp_str = line.split(' - ')[0]
                            log_time = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                            
                            if log_time > recent_cutoff:
                                processing_lines.append(line)
                        except:
                            continue
                
                if processing_lines:
                    # Parse the most recent processing line
                    latest_line = processing_lines[0]
                    
                    # Extract progress info: "Processing 51/400: Naeem (46761545684)"
                    if 'Processing' in latest_line:
                        try:
                            parts = latest_line.split('Processing ')[1].split(':')
                            progress_part = parts[0].strip()  # "51/400"
                            contact_part = parts[1].strip() if len(parts) > 1 else ""
                            
                            if '/' in progress_part:
                                current, total = progress_part.split('/')
                                current = int(current.strip())
                                total = int(total.strip())
                                
                                # Extract contact name and phone
                                contact_name = "Unknown"
                                contact_phone = ""
                                
                                if contact_part:
                                    # Parse "Naeem (46761545684)"
                                    if '(' in contact_part and ')' in contact_part:
                                        contact_name = contact_part.split('(')[0].strip()
                                        contact_phone = contact_part.split('(')[1].split(')')[0].strip()
                                    else:
                                        contact_name = contact_part
                                
                                return jsonify({
                                    "status": "processing",
                                    "progress": {
                                        "current": current,
                                        "total": total,
                                        "contact_name": contact_name,
                                        "contact_phone": contact_phone
                                    }
                                })
                        except Exception as e:
                            api_logger.warning(f"Error parsing WATI progress: {e}")
                
            except Exception as e:
                api_logger.warning(f"Error reading WATI progress from logs: {e}")
        
        # Default response - no active processing
        return jsonify({
            "status": "idle",
            "message": "No active WATI processing detected"
        })
        
    except Exception as e:
        log_error(e, f"API: WATI progress check failed for user {current_user.username}")
        api_logger.error(f"API: Error getting WATI progress for {current_user.username}: {str(e)}")
        
        return jsonify({"status": "error", "message": str(e)})


@log_function_call(api_logger)
def new_chat_session():
    """Start a new chat session"""
    api_logger.info(f"API: New chat session requested by user {current_user.username}")
    
    try:
        session_id = secrets.token_urlsafe(16)
        
        api_logger.info(f"API: New chat session created: {session_id} for user {current_user.username}")
        log_user_action("API: New Chat Session", current_user.id, f"Session: {session_id}")
        
        return jsonify({
            "success": True,
            "session_id": session_id,
            "message": "New chat session created"
        })
        
    except Exception as e:
        log_error(e, f"API: New chat session failed for user {current_user.username}")
        api_logger.error(f"API: Error creating new session for {current_user.username}: {str(e)}")
        
        return jsonify({"success": False, "error": str(e)})


@log_function_call(api_logger)
def get_logs():
    """Get recent logs for the process logs section"""
    api_logger.info(f"API: Get logs requested by user {current_user.username}")
    
    # Import here to avoid circular imports
    import app
    
    logs = []
    temp_queue = queue.Queue()
    
    # Get all logs from queue
    while not app.log_queue.empty():
        try:
            log_entry = app.log_queue.get_nowait()
            logs.append(log_entry)
            temp_queue.put(log_entry)  # Keep for other requests
        except queue.Empty:
            break
    
    # Put logs back in queue
    while not temp_queue.empty():
        try:
            app.log_queue.put_nowait(temp_queue.get_nowait())
        except queue.Full:
            break
    
    api_logger.info(f"API: Returned {len(logs)} log entries to user {current_user.username}")
    log_user_action("API: Get Logs", current_user.id, f"Logs: {len(logs)}")
    
    return jsonify(logs)


@log_function_call(api_logger)
def stream_logs():
    """Server-Sent Events stream for real-time logs"""
    from flask import Response
    # Import here to avoid circular imports
    import app
    
    # Capture user info at the start since current_user might become None during streaming
    username = current_user.username if current_user.is_authenticated else "anonymous"
    user_id = current_user.id if current_user.is_authenticated else None
    
    api_logger.info(f"API: Log stream started for user {username}")
    if user_id:
        log_user_action("API: Start Log Stream", user_id, "Real-time log streaming")
    
    def generate():
        # Create a queue for this subscriber
        subscriber_queue = queue.Queue(maxsize=100)
        app.log_subscribers.append(subscriber_queue)
        
        try:
            # Send existing logs first
            existing_logs = []
            temp_queue = queue.Queue()
            
            while not app.log_queue.empty():
                try:
                    log_entry = app.log_queue.get_nowait()
                    existing_logs.append(log_entry)
                    temp_queue.put(log_entry)
                except queue.Empty:
                    break
            
            # Put logs back
            while not temp_queue.empty():
                try:
                    app.log_queue.put_nowait(temp_queue.get_nowait())
                except queue.Full:
                    break
            
            # Send existing logs
            for log_entry in existing_logs[-20:]:  # Send last 20 logs
                yield f"data: {json.dumps(log_entry)}\n\n"
            
            # Stream new logs
            while True:
                try:
                    log_entry = subscriber_queue.get(timeout=30)  # 30 second timeout
                    yield f"data: {json.dumps(log_entry)}\n\n"
                except queue.Empty:
                    # Send heartbeat
                    yield f"data: {json.dumps({'type': 'heartbeat'})}\n\n"
                    
        except GeneratorExit:
            # Client disconnected
            if subscriber_queue in app.log_subscribers:
                app.log_subscribers.remove(subscriber_queue)
            api_logger.info(f"API: Log stream ended for user {username} (client disconnected)")
        except Exception as e:
            # Remove subscriber on error
            if subscriber_queue in app.log_subscribers:
                app.log_subscribers.remove(subscriber_queue)
            api_logger.error(f"API: Log stream error for user {username}: {str(e)}")
    
    return Response(generate(), mimetype='text/event-stream')