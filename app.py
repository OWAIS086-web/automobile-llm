import os
import secrets
import logging
import queue
import json
import sys
from datetime import timedelta, datetime
from flask import Flask, Response,render_template,jsonify
from flask_login import LoginManager, login_required, current_user
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import configuration system
from config.config_loader import get_config

# Initialize configuration
config = get_config()

# Import logging system with config
from utils.logger import server_logger, log_function_call, log_error, init_logging

# Initialize logging with configuration
init_logging(config.get_logging_config())

# Suppress verbose infrastructure logs (keep only RAG/LLM logs)
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('openai').setLevel(logging.WARNING)
logging.getLogger('openai._base_client').setLevel(logging.WARNING)
logging.getLogger('server').setLevel(logging.WARNING)
logging.getLogger('api').setLevel(logging.WARNING)
logging.getLogger('auth').setLevel(logging.WARNING)
logging.getLogger('chat').setLevel(logging.WARNING)
logging.getLogger('database').setLevel(logging.WARNING)
logging.getLogger('user').setLevel(logging.WARNING)
logging.getLogger('models.chat').setLevel(logging.WARNING)
logging.getLogger('controllers.chat').setLevel(logging.WARNING)
logging.getLogger('controllers.api').setLevel(logging.WARNING)
logging.getLogger('controllers.ai_analysis').setLevel(logging.WARNING)

# Import models and initialize database
from models import User, init_db

# Import controllers
from controllers import auth, api, analytics, whatsapp, chat, main, settings, facebook

# Configuration from config file
DATA_DIR = config.get('database.db_file', 'data').split('/')[0]  # Extract directory
os.makedirs(DATA_DIR, exist_ok=True)

# Initialize Flask app with configuration
app = Flask(__name__)
flask_config = config.get_flask_config()
app.config.update(flask_config)

server_logger.info("Flask application starting...")
server_logger.info(f"Data directory: {DATA_DIR}")
server_logger.info(f"Secret key configured: {'Yes' if config.get('server.secret_key') else 'No (using generated)'}")
server_logger.info(f"Debug mode: {config.get('server.debug', False)}")
server_logger.info(f"Host: {config.get('server.host', '127.0.0.1')}")
server_logger.info(f"Port: {config.get('server.port', 10000)}")

# Real-time log capture system
log_queue = queue.Queue(maxsize=1000)
log_subscribers = []

class LogCapture(logging.Handler):
    """Custom logging handler to capture logs for real-time display"""
    
    def emit(self, record):
        try:
            from datetime import datetime
            # Format the log message
            log_entry = {
                'timestamp': datetime.now().strftime('%H:%M:%S'),
                'level': record.levelname.lower(),
                'message': self.format(record)
            }
            
            # Add to queue (remove oldest if full)
            try:
                log_queue.put_nowait(log_entry)
            except queue.Full:
                try:
                    log_queue.get_nowait()
                    log_queue.put_nowait(log_entry)
                except queue.Empty:
                    pass
            
            # Notify all subscribers
            for subscriber in log_subscribers[:]:
                try:
                    subscriber.put_nowait(log_entry)
                except queue.Full:
                    log_subscribers.remove(subscriber)
                except:
                    if subscriber in log_subscribers:
                        log_subscribers.remove(subscriber)
                        
        except Exception as e:
            pass  # Avoid logging errors in the logger


class StdoutCapture:
    """Capture stdout/stderr for tqdm progress bars and other console output"""
    
    def __init__(self, original_stream, stream_name):
        self.original_stream = original_stream
        self.stream_name = stream_name
        self.buffer = ""
        self.enabled = True
    
    def write(self, text):
        # Always write to original stream first
        try:
            self.original_stream.write(text)
            self.original_stream.flush()
        except:
            pass  # Don't let capture errors break the original stream
        
        # Only capture if enabled and not in Flask's internal operations
        if not self.enabled or not text or not text.strip():
            return
        
        # Skip Flask internal messages that might interfere with server
        if any(skip_pattern in text for skip_pattern in [
            'werkzeug', 'serving.py', 'socketserver.py', 'selectors.py',
            'Thread-', 'serve_forever', 'socket', 'OSError'
        ]):
            return
        
        try:
            self.buffer += text
            
            # Check for complete lines or progress updates
            if '\n' in text or '\r' in text or any(keyword in text for keyword in [
                'Enriching blocks', 'Pipeline completed', 'Block separation', 
                'MixBlock', 'HavalPipeline', 'Starting pipeline', 'Scraping', 'Fetching',
                'WATI', 'WhatsApp', 'contacts', 'messages', 'import completed'
            ]):
                lines = self.buffer.replace('\r', '\n').split('\n')
                
                for line in lines[:-1]:  # Process all complete lines
                    line = line.strip()
                    if line and any(keyword in line for keyword in [
                        'Enriching blocks', 'Pipeline completed', 'Block separation',
                        'MixBlock', 'HavalPipeline', 'Starting pipeline', 'Scraping',
                        'Fetching', '🤖', '📡', '✅', '[07:', 'posts to database',
                        'WATI', 'WhatsApp', 'contacts', 'messages', 'import completed',
                        'Starting WATI', 'Processing contact', 'messages imported'
                    ]):
                        # Create log entry for progress updates
                        log_entry = {
                            'timestamp': datetime.now().strftime('%H:%M:%S'),
                            'level': 'info',
                            'message': line
                        }
                        
                        # Add to queue safely
                        try:
                            log_queue.put_nowait(log_entry)
                        except queue.Full:
                            try:
                                log_queue.get_nowait()
                                log_queue.put_nowait(log_entry)
                            except:
                                pass
                        except:
                            pass  # Don't let logging errors break the capture
                        
                        # Notify subscribers safely
                        for subscriber in log_subscribers[:]:
                            try:
                                subscriber.put_nowait(log_entry)
                            except:
                                try:
                                    if subscriber in log_subscribers:
                                        log_subscribers.remove(subscriber)
                                except:
                                    pass
                
                # Keep the last incomplete line
                self.buffer = lines[-1] if lines else ""
        except:
            pass  # Don't let capture errors break anything
    
    def flush(self):
        try:
            self.original_stream.flush()
        except:
            pass
    
    def disable(self):
        """Disable capture temporarily"""
        self.enabled = False
    
    def enable(self):
        """Re-enable capture"""
        self.enabled = True
    
    def __getattr__(self, name):
        return getattr(self.original_stream, name)


# Set up log capture
log_capture = LogCapture()
log_capture.setLevel(logging.INFO)
formatter = logging.Formatter('%(message)s')
log_capture.setFormatter(formatter)

# Add to app logger
app.logger.addHandler(log_capture)
app.logger.setLevel(logging.INFO)

# Add log capture handler to all our custom loggers
from utils.logger import (
    user_logger, server_logger, error_logger, scraping_logger, 
    fetching_logger, warning_logger, ai_logger, database_logger,
    auth_logger, api_logger, analytics_logger, whatsapp_logger, chat_logger
)

# Add the log capture handler to all loggers so they appear in the web stream
for logger in [user_logger, server_logger, error_logger, scraping_logger, 
               fetching_logger, warning_logger, ai_logger, database_logger,
               auth_logger, api_logger, analytics_logger, whatsapp_logger, chat_logger]:
    logger.addHandler(log_capture)

server_logger.info("Log capture system initialized")

# Set up stdout/stderr capture for tqdm progress bars (with safety checks)
try:
    original_stdout = sys.stdout
    original_stderr = sys.stderr
    
    # Only enable stdout capture if not in production or if explicitly enabled
    enable_stdout_capture = config.get('development.hot_reload', True)
    
    if enable_stdout_capture:
        sys.stdout = StdoutCapture(original_stdout, 'stdout')
        sys.stderr = StdoutCapture(original_stderr, 'stderr')
        server_logger.info("Stdout/stderr capture initialized for progress monitoring")
    else:
        server_logger.info("Stdout/stderr capture disabled (production mode)")
        
except Exception as e:
    server_logger.warning(f"Failed to initialize stdout capture: {e}")
    # Continue without stdout capture if it fails

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

@login_manager.user_loader
@log_function_call(server_logger)
def load_user(user_id):
    return User.get(int(user_id))

server_logger.info("Flask-Login initialized")

# Initialize database
try:
    init_db()
    server_logger.info("Database initialized successfully")
except Exception as e:
    log_error(e, "Database initialization failed")
    raise

# Initialize AI pipeline on startup
try:
    server_logger.info("Initializing AI pipeline...")
    from ai.haval_pipeline import get_pipeline_status, get_rag_engine
    
    # Check if pipeline is ready
    status = get_pipeline_status()
    server_logger.info(f"Pipeline status: {status.get('status', 'unknown')}")
    
    # Try to initialize RAG engine
    rag_engine = get_rag_engine()
    if rag_engine:
        server_logger.info("RAG engine initialized successfully")
    else:
        server_logger.warning("RAG engine not available - may need data processing")
        
except Exception as e:
    log_error(e, "AI pipeline initialization failed")
    server_logger.warning("AI features may not be available until data is processed")

# Lazy initialization functions for AI components
openai_client = None
llm_client = None

@log_function_call(server_logger)
def get_openai_client():
    """Lazy initialization of OpenAI client for Insights mode"""
    global openai_client
    if openai_client is not None:
        return openai_client

    try:
        from config import get_llm_for_component
        openai_client = get_llm_for_component("insights")
        server_logger.info("OpenAI client initialized for Insights mode")
        return openai_client
    except Exception as e:
        openai_client = False
        log_error(e, "Failed to initialize Insights LLM")
        return None

@log_function_call(server_logger)
def get_llm_client():
    """Lazy initialization of LLM client"""
    global llm_client
    if llm_client is not None:
        return llm_client

    try:
        from config import get_llm_for_component
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        llm_client = get_llm_for_component("answer_generation", fallback_api_key=gemini_api_key)
        server_logger.info("LLM client initialized from centralized config")
        return llm_client
    except Exception as e:
        llm_client = False
        log_error(e, "Failed to initialize LLM client")
        return None

# ----------------------
# ROUTES - Using MVC Controllers
# ----------------------

# Authentication Routes
@app.route("/login", methods=["GET", "POST"])
@log_function_call(server_logger)
def login():
    return auth.login()

@app.route("/register", methods=["GET", "POST"])
@log_function_call(server_logger)
def register():
    return auth.register()

@app.route("/logout")
@login_required
@log_function_call(server_logger)
def logout():
    return auth.logout()

# Main Routes
@app.route("/")
@log_function_call(server_logger)
def index():
    """Landing page for non-authenticated users"""
    return render_template('landing.html')

@app.route("/help")
@log_function_call(server_logger)
def help_page():
    """Help center page"""
    return render_template('help.html')

@app.route("/download_file")
@log_function_call(server_logger)
def download_file():
    return main.download_file()

@app.route("/scrape_single_topic", methods=["POST"])
@login_required
@log_function_call(server_logger)
def scrape_single_topic():
    return main.scrape_single_topic()

@app.route("/pipeline_status")
@log_function_call(server_logger)
def pipeline_status():
    return main.pipeline_status()

# Chat Routes
@app.route("/chatbot")
@login_required
@log_function_call(server_logger)
def chatbot():
    return chat.chatbot()

@app.route("/chatbot_advanced")
@login_required
@log_function_call(server_logger)
def chatbot_advanced():
    return chat.chatbot_advanced()

@app.route("/api/auth/status", methods=["GET"])
def auth_status():
    """Check if user is authenticated"""
    try:
        is_authenticated = current_user.is_authenticated
        username = current_user.username if is_authenticated else None
        user_id = current_user.id if is_authenticated else None
        
        # Add debug logging
        from utils.logger import server_logger
        server_logger.info(f"Auth status check: authenticated={is_authenticated}, username={username}, user_id={user_id}")
        
        return jsonify({
            "authenticated": is_authenticated,
            "username": username,
            "user_id": user_id
        })
    except Exception as e:
        from utils.logger import server_logger, log_error
        log_error(e, "Error in auth status check")
        return jsonify({
            "authenticated": False,
            "username": None,
            "error": str(e)
        })

@app.route("/api/debug/session", methods=["GET"])
def debug_session():
    """Debug session information"""
    try:
        from flask import session
        return jsonify({
            "session_keys": list(session.keys()),
            "has_user_id": '_user_id' in session,
            "current_user_authenticated": current_user.is_authenticated,
            "current_user_id": getattr(current_user, 'id', None),
            "current_user_username": getattr(current_user, 'username', None)
        })
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route("/api/debug/chat-history", methods=["GET"])
@login_required
def debug_chat_history():
    """Debug chat history data"""
    try:
        from models.chat import get_user_chat_history
        from flask import request
        
        # Get parameters
        mode = request.args.get('mode', 'insights')
        limit = int(request.args.get('limit', 10))
        
        # Get current session ID
        from flask import session
        session_id = session.get('chat_session_id', 'no-session')
        
        # Get chat history
        history = get_user_chat_history(current_user.id, mode, session_id, limit=limit)
        
        # Also get raw database data
        from models import get_db_connection
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT id, user_id, session_id, mode, query, response, 
                   timestamp
            FROM chat_history 
            WHERE user_id = ? 
            ORDER BY timestamp DESC 
            LIMIT ?
        """, (current_user.id, limit))
        
        raw_data = []
        for row in cur.fetchall():
            raw_data.append({
                'id': row[0],
                'user_id': row[1],
                'session_id': row[2],
                'mode': row[3],
                'user_message': row[4][:100] + '...' if len(row[4]) > 100 else row[4],
                'bot_response': row[5][:100] + '...' if len(row[5]) > 100 else row[5],
                'timestamp': row[6]
            })
        
        conn.close()
        
        return jsonify({
            "current_user_id": current_user.id,
            "current_session_id": session_id,
            "mode": mode,
            "processed_history_count": len(history),
            "processed_history": history[:5],  # First 5 for brevity
            "raw_database_count": len(raw_data),
            "raw_database_data": raw_data[:5],  # First 5 for brevity
            "all_sessions": list(set([row['session_id'] for row in raw_data]))
        })
        
    except Exception as e:
        log_error(e, "Error in debug chat history")
        return jsonify({"error": str(e)})

@app.route("/api/debug/test-chat-save", methods=["POST"])
@login_required
def debug_test_chat_save():
    """Test saving a chat message"""
    try:
        from models.chat import save_user_chat_history
        from flask import session
        import secrets
        
        # Get or create session ID
        session_id = session.get('chat_session_id')
        if not session_id:
            session_id = secrets.token_hex(16)
            session['chat_session_id'] = session_id
        
        # Test data
        test_query = "Test message from debug endpoint"
        test_response = "Test response from debug endpoint"
        test_mode = "insights"
        
        # Save the test chat
        save_user_chat_history(current_user.id, session_id, test_mode, test_query, test_response)
        
        return jsonify({
            "success": True,
            "message": "Test chat saved successfully",
            "user_id": current_user.id,
            "session_id": session_id,
            "mode": test_mode
        })
        
    except Exception as e:
        log_error(e, "Error in test chat save")
        return jsonify({"error": str(e), "success": False})

@app.route("/api/debug/test-followups", methods=["POST"])
@login_required
def debug_test_followups():
    """Test follow-up generation functionality"""
    try:
        data = request.get_json()
        test_query = data.get('query', 'What are the problems with Haval H6?')
        test_answer = data.get('answer', 'There are several issues reported with Haval H6 including engine problems, electrical issues, and transmission concerns.')
        
        # Import the follow-up generation function
        from controllers.ai_analysis import generate_followup_questions, extract_structured_data
        
        # Test follow-up generation
        followups = generate_followup_questions([], test_answer)
        
        # Test structured data extraction
        structured = extract_structured_data(test_answer, [], 'pakwheels')
        
        return jsonify({
            "success": True,
            "test_query": test_query,
            "test_answer": test_answer,
            "generated_followups": followups,
            "structured_data": structured,
            "followups_count": len(followups),
            "has_followups_in_structured": 'followups' in structured and len(structured['followups']) > 0
        })
        
    except Exception as e:
        server_logger.error(f"Error in debug_test_followups: {e}")
        return jsonify({"error": str(e), "success": False})

@app.route("/chatbot_query", methods=["POST"])
@login_required
@log_function_call(server_logger)
def chatbot_query():
    """Process chatbot queries - debug version"""
    try:
        # Add debug logging
        server_logger.info(f"Chatbot query endpoint hit by user: {current_user.username if current_user.is_authenticated else 'Anonymous'}")
        server_logger.info(f"User authenticated: {current_user.is_authenticated}")
        
        return chat.chatbot_query()
    except Exception as e:
        log_error(e, "Error in chatbot_query endpoint")
        return jsonify({"answer": f"Error: {str(e)}"})

@app.route("/chatbot_query_stream", methods=["POST"])
@login_required
@log_function_call(server_logger)
def chatbot_query_stream():
    return chat.chatbot_query_stream()

@app.route("/chatbot_query_fast", methods=["POST"])
@login_required
@log_function_call(server_logger)
def chatbot_query_fast():
    return chat.chatbot_query_fast()

# API Routes
@app.route("/api/test/facebook-beta", methods=["POST"])
@log_function_call(server_logger)
def test_facebook_beta():
    """Test endpoint for Facebook Beta mode without authentication"""
    try:
        from flask import request
        from services.ai_service import AIService
        
        data = request.get_json() or {}
        query = data.get("query", "recent issues")
        
        # Test Facebook Beta mode directly
        answer = AIService.process_chat_query(query, "facebook_beta", "haval")
        
        return jsonify({
            "answer": answer,
            "status": "success"
        })
        
    except Exception as e:
        from utils.logger import log_error
        log_error(e, "Test Facebook Beta endpoint error")
        return jsonify({
            "answer": f"Error: {str(e)}",
            "status": "error"
        })

@app.route("/api/company", methods=["GET"])
@login_required
@log_function_call(server_logger)
def get_selected_company():
    return api.get_selected_company()

@app.route("/api/company", methods=["POST"])
@login_required
@log_function_call(server_logger)
def set_selected_company():
    return api.set_selected_company()

@app.route("/api/companies", methods=["GET"])
@login_required
@log_function_call(server_logger)
def get_all_companies_api():
    return api.get_all_companies_api()

@app.route("/api/chat/sessions", methods=["GET"])
@login_required
@log_function_call(server_logger)
def get_chat_sessions():
    return api.get_chat_sessions()

@app.route("/api/chat/history/<session_id>", methods=["GET"])
@login_required
@log_function_call(server_logger)
def get_session_history(session_id):
    return api.get_session_history(session_id)

@app.route("/api/chat/session/<session_id>", methods=["DELETE"])
@login_required
@log_function_call(server_logger)
def delete_chat_session(session_id):
    return api.delete_chat_session(session_id)

@app.route("/api/chat/clear", methods=["POST"])
@login_required
@log_function_call(server_logger)
def clear_chat_history():
    return api.clear_chat_history()

@app.route("/api/pipeline-status", methods=["GET"])
@log_function_call(server_logger)
def api_pipeline_status():
    return api.api_pipeline_status()

@app.route("/api/wati/progress", methods=["GET"])
@login_required
@log_function_call(server_logger)
def get_wati_progress():
    return api.get_wati_progress()

@app.route("/api/chat/new-session", methods=["POST"])
@login_required
@log_function_call(server_logger)
def new_chat_session():
    return api.new_chat_session()

@app.route("/api/current-model", methods=["GET"])
@login_required
@log_function_call(server_logger)
def api_current_model():
    """Get current AI model configuration"""
    try:
        from config.llm_config import get_llm_config
        
        # Get the main answer generation model config
        config = get_llm_config("answer_generation")
        
        return jsonify({
            "success": True,
            "provider": config.provider,
            "model_name": config.model_name,
            "temperature": config.temperature,
            "max_tokens": config.max_tokens
        })
        
    except Exception as e:
        server_logger.error(f"Error getting current model: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "provider": "grok",  # Default fallback
            "model_name": "grok-3-fast"
        })

# Dealership Management Routes
@app.route("/dealership")
@login_required
@log_function_call(server_logger)
def dealership_dashboard():
    import controllers.dealership as dealership
    return dealership.dealership_dashboard()

@app.route("/dealership/warranty-claims")
@login_required
@log_function_call(server_logger)
def warranty_claims():
    import controllers.dealership as dealership
    return dealership.warranty_claims()

@app.route("/dealership/campaign-reports")
@login_required
@log_function_call(server_logger)
def campaign_reports():
    import controllers.dealership as dealership
    return dealership.campaign_reports()

@app.route("/dealership/ffs-inspections")
@login_required
@log_function_call(server_logger)
def ffs_inspections():
    import controllers.dealership as dealership
    return dealership.ffs_inspections()

@app.route("/dealership/sfs-inspections")
@login_required
@log_function_call(server_logger)
def sfs_inspections():
    import controllers.dealership as dealership
    return dealership.sfs_inspections()

@app.route("/dealership/pdi-inspections")
@login_required
@log_function_call(server_logger)
def pdi_inspections():
    import controllers.dealership as dealership
    return dealership.pdi_inspections()

@app.route("/dealership/repair-orders")
@login_required
@log_function_call(server_logger)
def repair_orders():
    import controllers.dealership as dealership
    return dealership.repair_orders()

@app.route("/dealership/vin-history")
@login_required
@log_function_call(server_logger)
def vin_history():
    import controllers.dealership as dealership
    return dealership.vin_history()

# Dealership API Routes
@app.route("/api/dealership/tyre-complaints")
@login_required
@log_function_call(server_logger)
def api_tyre_complaints():
    import controllers.dealership as dealership
    return dealership.api_tyre_complaints()

@app.route("/api/dealership/stats")
@login_required
@log_function_call(server_logger)
def api_dealership_stats():
    import controllers.dealership as dealership
    return dealership.api_dealership_stats()

@app.route("/api/dealership/export")
@login_required
@log_function_call(server_logger)
def export_dealership_data():
    import controllers.dealership as dealership
    return dealership.export_data()

@app.route("/api/ai-analysis", methods=["POST"])
@login_required
@log_function_call(server_logger)
def ai_analysis_query():
    """Direct AI analysis endpoint for intelligent query processing"""
    try:
        data = request.get_json(force=True) or {}
        query = (data.get("query") or "").strip()
        
        if not query:
            return jsonify({"answer": "Please provide a query for analysis."})
        
        from controllers.ai_analysis import ai_analyze_query
        from models import get_db_connection
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Use AI analysis for intelligent responses
        answer = ai_analyze_query(query, cur)
        conn.close()
        
        return jsonify({
            "answer": answer,
            "structured": {"references": [], "charts": [], "tables": [], "recommendations": []}
        })
        
    except Exception as e:
        log_error(e, f"AI Analysis error for user {current_user.username}")
        return jsonify({
            "answer": "Sorry, the AI analysis encountered an error. Please try again."
        })

@app.route("/api/logs")
@login_required
@log_function_call(server_logger)
def get_logs():
    return api.get_logs()

@app.route("/api/logs/stream")
@login_required
@log_function_call(server_logger)
def stream_logs():
    return api.stream_logs()

# Analytics Routes
@app.route("/analysis")
@login_required
@log_function_call(server_logger)
def analysis():
    return analytics.analysis()

@app.route("/generate_report", methods=['GET', 'POST'])
@login_required
@log_function_call(server_logger)
def generate_report():
    return analytics.generate_report()

@app.route("/db_summary")
@login_required
@log_function_call(server_logger)
def db_summary():
    return analytics.db_summary()

# WhatsApp Routes
@app.route("/view_whatsapp")
@login_required
@log_function_call(server_logger)
def view_whatsapp():
    return whatsapp.view_whatsapp()

@app.route("/debug_whatsapp")
@login_required
@log_function_call(server_logger)
def debug_whatsapp():
    return whatsapp.debug_whatsapp()

@app.route("/view_whatsapp/<path:customer_name>")
@login_required
@log_function_call(server_logger)
def view_whatsapp_by_customer(customer_name):
    return whatsapp.view_whatsapp_by_customer(customer_name)

@app.route("/fetch_wati_data", methods=["POST"])
@login_required
@log_function_call(server_logger)
def fetch_wati_data():
    return whatsapp.fetch_wati_data()

# Facebook Routes
@app.route("/view_facebook")
@login_required
@log_function_call(server_logger)
def view_facebook():
    return facebook.view_facebook()

@app.route("/api/facebook/posts")
@login_required
@log_function_call(server_logger)
def api_facebook_posts():
    return facebook.api_facebook_posts()

@app.route("/api/facebook/stats")
@login_required
@log_function_call(server_logger)
def api_facebook_stats():
    return facebook.api_facebook_stats()

@app.route("/api/facebook/insights")
@login_required
@log_function_call(server_logger)
def api_facebook_issue_insights():
    return facebook.api_facebook_issue_insights()

@app.route("/api/facebook/process", methods=["POST"])
@login_required
@log_function_call(server_logger)
def api_process_facebook_data():
    return facebook.api_process_facebook_data()

# Settings Routes
@app.route("/settings")
@login_required
@log_function_call(server_logger)
def settings_page():
    return settings.settings_page()

@app.route("/update_settings", methods=["POST"])
@login_required
@log_function_call(server_logger)
def update_settings():
    return settings.update_settings()

@app.route("/api/settings")
@login_required
@log_function_call(server_logger)
def get_settings_api():
    return settings.get_settings_api()

@app.route("/reset_settings", methods=["POST"])
@login_required
@log_function_call(server_logger)
def reset_settings():
    return settings.reset_settings()

@app.route("/export_settings")
@login_required
@log_function_call(server_logger)
def export_settings():
    return settings.export_settings()

@app.route("/import_settings", methods=["POST"])
@login_required
@log_function_call(server_logger)
def import_settings():
    return settings.import_settings()

@app.route("/restart_server", methods=["POST"])
@login_required
@log_function_call(server_logger)
def restart_server():
    return settings.restart_server()

# Logging Management API Routes
@app.route("/api/logging_status")
@login_required
@log_function_call(server_logger)
def get_logging_status():
    return settings.get_logging_status()

@app.route("/api/rotate_logs", methods=["POST"])
@login_required
@log_function_call(server_logger)
def rotate_logs():
    return settings.rotate_logs()

@app.route("/api/cleanup_logs", methods=["POST"])
@login_required
@log_function_call(server_logger)
def cleanup_logs():
    return settings.cleanup_logs()

@app.route("/api/set_logger_level", methods=["POST"])
@login_required
@log_function_call(server_logger)
def set_logger_level():
    return settings.set_logger_level()

@app.route("/api/download_log")
@login_required
@log_function_call(server_logger)
def download_log_file():
    return settings.download_log_file()

# Error handlers
@app.errorhandler(404)
@log_function_call(server_logger)
def not_found_error(error):
    server_logger.warning(f"404 error: {error}")
    return "Page not found", 404

@app.errorhandler(500)
@log_function_call(server_logger)
def internal_error(error):
    log_error(error, "Internal server error")
    return "Internal server error", 500

# ----------------------
# Application Entry Point
# ----------------------

if __name__ == "__main__":
    import logging
    
    # Get server configuration
    server_config = config.get_server_config()
    
    # Suppress SSL handshake errors and reduce noise
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    
    # Display startup information
    server_logger.info("="*70)
    server_logger.info(f"{config.get('app.name', 'Haval Marketing Tool')} - Version {config.get('app.version', '2.0')}")
    server_logger.info("="*70)
    server_logger.info("Server starting...")
    server_logger.info(f"Open your browser to: http://{server_config['host']}:{server_config['port']}/")
    server_logger.info(f"Debug mode: {server_config['debug']}")
    server_logger.info(f"Auto-reload: {server_config.get('use_reloader', False)}")
    server_logger.info(f"Threading: {server_config.get('threaded', True)}")
    server_logger.info("="*70)
    
    try:
        # Start Flask application with configuration
        app.run(**server_config)
    except KeyboardInterrupt:
        server_logger.info("Server shutdown requested")
        # Restore original stdout/stderr
        try:
            if hasattr(sys.stdout, 'original_stream'):
                sys.stdout = sys.stdout.original_stream
            if hasattr(sys.stderr, 'original_stream'):
                sys.stderr = sys.stderr.original_stream
        except:
            pass
    except Exception as e:
        log_error(e, "Failed to start Flask application")
        # Restore original stdout/stderr on error
        try:
            if 'original_stdout' in locals():
                sys.stdout = original_stdout
            if 'original_stderr' in locals():
                sys.stderr = original_stderr
        except:
            pass
        raise