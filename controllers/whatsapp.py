from flask import render_template, request, jsonify, flash, url_for
from flask_login import current_user, login_required
from models.whatsapp import WhatsAppMessage
from utils.logger import whatsapp_logger, log_function_call, log_user_action, log_error
import urllib.parse
import json
import os


@log_function_call(whatsapp_logger)
def view_whatsapp():
    """View all WhatsApp messages page with filtering options - Only for Haval users"""
    
    # Check if user has access to WhatsApp data (only Haval users)
    user_company = current_user.company_id or 'haval'
    whatsapp_logger.info(f"WhatsApp view accessed by user {current_user.username} (company: {user_company})")
    
    if user_company != 'haval':
        whatsapp_logger.warning(f"WhatsApp access denied for user {current_user.username} (company: {user_company})")
        log_user_action("WhatsApp Access Denied", current_user.id, f"Company: {user_company}")
        
        flash(f"WhatsApp data is only available for Haval users. You are registered as {user_company.title()} user.", "error")
        return render_template("access_denied.html", 
                             message="WhatsApp Access Restricted",
                             description=f"WhatsApp data is only available for Haval users. You are registered as a {user_company.title()} user.",
                             redirect_url=url_for('chatbot_advanced'),
                             redirect_text="Go to Chatbot")
    
    # Get filter parameters
    message_type_filter = request.args.get('type', 'all')
    customer_filter = request.args.get('customer', '')
    date_filter = request.args.get('date', 'all')
    
    whatsapp_logger.info(f"WhatsApp filters applied by {current_user.username}: type={message_type_filter}, customer={customer_filter}, date={date_filter}")
    
    try:
        # Get WhatsApp messages
        whatsapp_logger.info(f"Fetching WhatsApp messages for user {current_user.username}")
        messages = WhatsAppMessage.get_messages(
            company_id=user_company,
            message_type=message_type_filter,
            customer_name=customer_filter,
            date_filter=date_filter,
            limit=1000
        )
        
        # Get statistics
        whatsapp_logger.info(f"Fetching WhatsApp statistics for user {current_user.username}")
        stats = WhatsAppMessage.get_statistics(
            company_id=user_company,
            date_filter=date_filter
        )
        
        # Get unique customers for filter
        whatsapp_logger.info(f"Fetching unique customers for user {current_user.username}")
        customers = WhatsAppMessage.get_unique_customers(user_company)
        
        # Convert messages to dict format for template
        messages_list = []
        for msg in messages:
            messages_list.append({
                'id': msg.id,
                'customer_name': msg.customer_name,
                'country_code': msg.country_code,
                'contact_number': msg.contact_number,
                'message_type': msg.message_type,
                'message': msg.message,
                'timestamp': msg.timestamp,
                'imported_at': msg.imported_at,
                'phone_number': f"+{msg.country_code}{msg.contact_number}" if msg.country_code and msg.contact_number else "N/A"
            })
        
        whatsapp_logger.info(f"WhatsApp data loaded for {current_user.username}: {len(messages_list)} messages, {len(customers)} customers")
        log_user_action("WhatsApp View", current_user.id, 
                       f"Messages: {len(messages_list)}, Customers: {len(customers)}, Filters: type={message_type_filter}, date={date_filter}")
        
    except Exception as e:
        log_error(e, f"Error loading WhatsApp data for user {current_user.username}")
        whatsapp_logger.error(f"Error in view_whatsapp for {current_user.username}: {str(e)}")
        
        messages_list = []
        stats = {
            'total_messages': 0,
            'message_types': {},
            'unique_customers': 0,
            'daily_activity': {}
        }
        customers = []
    
    return render_template("view_whatsapp_pro.html", 
                         messages=messages_list,
                         stats=stats,
                         message_type_filter=message_type_filter,
                         customer_filter=customer_filter,
                         date_filter=date_filter,
                         customers=customers)


@log_function_call(whatsapp_logger)
def view_whatsapp_by_customer(customer_name):
    """Show all WhatsApp messages for a specific customer - Only for Haval users"""
    
    # Check if user has access to WhatsApp data (only Haval users)
    user_company = current_user.company_id or 'haval'
    
    # Decode the customer name from URL
    decoded_customer = urllib.parse.unquote(customer_name)
    
    whatsapp_logger.info(f"WhatsApp customer view accessed by user {current_user.username} for customer: {decoded_customer}")
    
    if user_company != 'haval':
        whatsapp_logger.warning(f"WhatsApp customer access denied for user {current_user.username} (company: {user_company})")
        log_user_action("WhatsApp Customer Access Denied", current_user.id, f"Company: {user_company}, Customer: {decoded_customer}")
        
        flash(f"WhatsApp data is only available for Haval users. You are registered as {user_company.title()} user.", "error")
        return render_template("access_denied.html", 
                             message="WhatsApp Access Restricted",
                             description=f"WhatsApp data is only available for Haval users. You are registered as a {user_company.title()} user.",
                             redirect_url=url_for('chatbot_advanced'),
                             redirect_text="Go to Chatbot")
    
    try:
        # Get all messages for this customer
        whatsapp_logger.info(f"Fetching messages for customer {decoded_customer} by user {current_user.username}")
        messages = WhatsAppMessage.get_messages_by_customer(decoded_customer, user_company)
        
        # Convert to dict format for template
        messages_list = []
        for msg in messages:
            messages_list.append({
                'id': msg.id,
                'customer_name': msg.customer_name,
                'country_code': msg.country_code,
                'contact_number': msg.contact_number,
                'message_type': msg.message_type,
                'message': msg.message,
                'timestamp': msg.timestamp,
                'imported_at': msg.imported_at,
                'phone_number': f"+{msg.country_code}{msg.contact_number}" if msg.country_code and msg.contact_number else "N/A"
            })
        
        whatsapp_logger.info(f"Customer messages loaded for {current_user.username}: {len(messages_list)} messages for {decoded_customer}")
        log_user_action("WhatsApp Customer View", current_user.id, 
                       f"Customer: {decoded_customer}, Messages: {len(messages_list)}")
        
    except Exception as e:
        log_error(e, f"Error getting customer messages for user {current_user.username}, customer {decoded_customer}")
        whatsapp_logger.error(f"Error getting customer messages for {current_user.username}: {str(e)}")
        messages_list = []
    
    return render_template("view_whatsapp_detail_pro.html", 
                         customer_name=decoded_customer, 
                         messages=messages_list,
                         total_messages=len(messages_list))


@log_function_call(whatsapp_logger)
def debug_whatsapp():
    """Debug route to check WhatsApp messages in database"""
    from models.database import get_db_connection
    
    whatsapp_logger.info(f"WhatsApp debug accessed by user {current_user.username}")
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Check if table exists
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='whatsapp_messages'")
        table_exists = cur.fetchone()
        
        if not table_exists:
            conn.close()
            whatsapp_logger.warning(f"WhatsApp debug: table does not exist for user {current_user.username}")
            return jsonify({"error": "whatsapp_messages table does not exist"})
        
        # Get table schema
        cur.execute("PRAGMA table_info(whatsapp_messages)")
        schema = cur.fetchall()
        
        # Get sample data
        cur.execute("SELECT * FROM whatsapp_messages LIMIT 5")
        sample_data = cur.fetchall()
        
        # Get count
        cur.execute("SELECT COUNT(*) FROM whatsapp_messages")
        total_count = cur.fetchone()[0]
        
        conn.close()
        
        debug_result = {
            "table_exists": True,
            "schema": [{"column": row[1], "type": row[2]} for row in schema],
            "total_count": total_count,
            "sample_data": [dict(row) for row in sample_data]
        }
        
        whatsapp_logger.info(f"WhatsApp debug completed for {current_user.username}: {total_count} total messages")
        log_user_action("WhatsApp Debug", current_user.id, f"Total messages: {total_count}")
        
        return jsonify(debug_result)
        
    except Exception as e:
        log_error(e, f"WhatsApp debug error for user {current_user.username}")
        whatsapp_logger.error(f"WhatsApp debug error for {current_user.username}: {str(e)}")
        return jsonify({"error": str(e)})


@log_function_call(whatsapp_logger)
def fetch_wati_data():
    """Fetch latest contacts and messages from WATI API - Only for Haval users"""
    
    # Check if user has access to WhatsApp data (only Haval users)
    user_company = current_user.company_id or 'haval'
    
    whatsapp_logger.info(f"WATI data fetch requested by user {current_user.username} (company: {user_company})")
    
    if user_company != 'haval':
        whatsapp_logger.warning(f"WATI access denied for user {current_user.username} (company: {user_company})")
        log_user_action("WATI Access Denied", current_user.id, f"Company: {user_company}")
        
        flash(f"WATI data access is only available for Haval users. You are registered as {user_company.title()} user.", "error")
        return render_template("access_denied.html", 
                             message="WATI Access Restricted",
                             description=f"WATI data access is only available for Haval users. You are registered as a {user_company.title()} user.",
                             redirect_url=url_for('chatbot_advanced'),
                             redirect_text="Go to Chatbot")
    
    try:
        # Get time period from form
        time_period = request.form.get('period', '24h')
        
        whatsapp_logger.info(f"WATI fetch started by {current_user.username}: period={time_period}")
        
        # Import WATI functionality
        from controllers.wati_integration import fetch_and_import_wati_data
        
        # Fetch data from WATI API
        whatsapp_logger.info(f"Calling WATI integration for user {current_user.username}")
        result = fetch_and_import_wati_data(user_company, time_period)
        
        if result['success']:
            messages_imported = result.get('messages_imported', 0)
            messages_skipped = result.get('messages_skipped', 0)
            contacts_fetched = result.get('contacts_fetched', 0)
            
            whatsapp_logger.info(f"WATI fetch successful for {current_user.username}: {messages_imported} imported, {messages_skipped} skipped, {contacts_fetched} contacts")
            log_user_action("WATI Fetch Success", current_user.id, 
                           f"Period: {time_period}, Imported: {messages_imported}, Skipped: {messages_skipped}, Contacts: {contacts_fetched}")
            
            flash(f"Successfully imported {messages_imported} new messages from WATI API.", "success")
            if messages_skipped > 0:
                flash(f"Skipped {messages_skipped} duplicate messages.", "info")
        else:
            error_msg = result.get('error', 'Unknown error')
            whatsapp_logger.error(f"WATI fetch failed for {current_user.username}: {error_msg}")
            log_user_action("WATI Fetch Failed", current_user.id, f"Period: {time_period}, Error: {error_msg}")
            
            flash(f"Error importing WATI data: {error_msg}", "error")
        
        return jsonify(result)
        
    except ImportError:
        error_msg = "WATI integration module not found"
        whatsapp_logger.error(f"WATI import error for {current_user.username}: {error_msg}")
        log_user_action("WATI Import Error", current_user.id, error_msg)
        
        flash("WATI integration is not available. Please check your configuration.", "error")
        return jsonify({
            "success": False,
            "error": error_msg
        })
    except Exception as e:
        error_msg = str(e)
        log_error(e, f"WATI fetch error for user {current_user.username}")
        whatsapp_logger.error(f"WATI fetch error for {current_user.username}: {error_msg}")
        log_user_action("WATI Fetch Error", current_user.id, f"Error: {error_msg}")
        
        flash(f"Error fetching WATI data: {error_msg}", "error")
        return jsonify({
            "success": False,
            "error": error_msg
        })