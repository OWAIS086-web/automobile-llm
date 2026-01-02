"""
WATI Integration Controller

Handles fetching WhatsApp messages and contacts from WATI API.
Integrates with the company configuration system and database.
"""

import requests
import json
import time
import re
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple
from flask import current_app
from models.whatsapp import WhatsAppMessage
from models.database import get_db_connection
from utils.logger import whatsapp_logger, fetching_logger, log_function_call, log_error
from config import get_company_config


def classify_whatsapp_message(text):
    """
    Enhanced WhatsApp message classification with more sophisticated logic
    Classifies as 'complaint', 'query', 'support', 'booking', or 'chat'
    """
    if not text:
        return "chat"
    
    text_lower = text.lower().strip()
    
    # Complaint indicators (enhanced from old project)
    complaint_keywords = [
        'problem', 'issue', 'broken', 'not working', 'defect', 'fault', 'error',
        'complaint', 'complain', 'disappointed', 'unhappy', 'frustrated', 'angry',
        'terrible', 'awful', 'bad', 'worst', 'horrible', 'useless', 'pathetic',
        'failed', 'failure', 'damage', 'damaged', 'wrong', 'incorrect', 'poor',
        'quality', 'service', 'delay', 'delayed', 'late', 'slow', 'stuck',
        'noise', 'noisy', 'vibration', 'shake', 'leak', 'leaking', 'smoke',
        'overheating', 'breakdown', 'repair', 'fix', 'replace', 'refund',
        'warranty', 'guarantee', 'compensation', 'money back', 'malfunction',
        'trouble', 'troublesome', 'defective', 'faulty', 'unsatisfied'
    ]
    
    # Query indicators (enhanced)
    query_keywords = [
        'how', 'what', 'when', 'where', 'why', 'which', 'who', 'can you',
        'could you', 'would you', 'please tell', 'please help', 'i want to know',
        'information', 'details', 'explain', 'clarify', 'confirm', 'check',
        'availability', 'available', 'price', 'cost', 'features', 'specifications', 
        'compare', 'difference', 'better', 'recommend', 'suggest', 'advice', 
        'opinion', 'review', 'feedback', 'tell me about', 'show me'
    ]
    
    # Support/Service indicators
    support_keywords = [
        'help', 'support', 'assistance', 'service', 'technician', 'mechanic',
        'appointment', 'schedule', 'visit', 'inspection', 'maintenance',
        'servicing', 'checkup', 'repair shop', 'service center'
    ]
    
    # Booking/Sales indicators
    booking_keywords = [
        'booking', 'book', 'reserve', 'test drive', 'purchase', 'buy', 'buying',
        'delivery', 'order', 'payment', 'installment', 'finance', 'loan',
        'showroom', 'dealer', 'sales', 'quotation', 'quote'
    ]
    
    # Check for question marks and exclamation marks
    has_question_mark = '?' in text
    has_exclamation = '!' in text
    
    # Count indicators for each category
    complaint_score = sum(1 for keyword in complaint_keywords if keyword in text_lower)
    query_score = sum(1 for keyword in query_keywords if keyword in text_lower)
    support_score = sum(1 for keyword in support_keywords if keyword in text_lower)
    booking_score = sum(1 for keyword in booking_keywords if keyword in text_lower)
    
    # Enhanced classification logic
    if booking_score > 0 and (booking_score >= max(complaint_score, query_score, support_score)):
        return "booking"
    elif support_score > 0 and (support_score >= max(complaint_score, query_score)):
        return "support"
    elif has_question_mark and query_score > 0:
        return "query"
    elif complaint_score > 0 and (has_exclamation or complaint_score > query_score):
        return "complaint"
    elif query_score > complaint_score and query_score > 0:
        return "query"
    elif has_question_mark:
        return "query"
    elif complaint_score > 0:
        return "complaint"
    elif support_score > 0:
        return "support"
    else:
        return "chat"


class WATIClient:
    """WATI API client for fetching WhatsApp data"""
    
    def __init__(self, api_token: str, tenant_id: str, api_base: str = "https://live-mt-server.wati.io"):
        self.api_token = api_token
        self.tenant_id = tenant_id
        self.api_base = api_base
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }
    
    def get_contacts(self, page_size: int = 400, since_hours: int = 24) -> List[Dict]:
        """Fetch contacts updated in the last N hours"""
        fetching_logger.info(f"Fetching WATI contacts updated in last {since_hours} hours")
        
        page = 1
        all_contacts = []
        now = datetime.now(timezone.utc)
        since_time = now - timedelta(hours=since_hours)
        
        while True:
            url = f"{self.api_base}/{self.tenant_id}/api/v1/getContacts"
            params = {"pageNumber": page, "pageSize": page_size}
            
            try:
                response = requests.get(url, headers=self.headers, params=params, timeout=30)
                response.raise_for_status()
                
                data = response.json()
                contact_list = data.get("contact_list", [])
                
                if not contact_list:
                    whatsapp_logger.info(f"No more contacts found on page {page}")
                    break
                
                page_has_recent = False
                
                for contact in contact_list:
                    last_updated = contact.get("updatedAt")
                    if last_updated:
                        try:
                            contact_time = datetime.fromisoformat(last_updated.replace("Z", "+00:00"))
                            if contact_time.tzinfo is None:
                                contact_time = contact_time.replace(tzinfo=timezone.utc)
                        except Exception as e:
                            whatsapp_logger.warning(f"Failed to parse contact timestamp {last_updated}: {e}")
                            continue
                        
                        if contact_time >= since_time:
                            page_has_recent = True
                        else:
                            continue  # Skip older contacts
                    
                    # Extract name and phone
                    name = None
                    phone = None
                    
                    for param in contact.get("customParams", []):
                        if param["name"].lower() == "name":
                            name = param["value"]
                        if param["name"].lower() == "phone":
                            phone = param["value"]
                    
                    if not name:
                        name = contact.get("fullName") or contact.get("firstName")
                    if not phone:
                        phone = contact.get("phone")
                    
                    if phone:
                        all_contacts.append({
                            "name": name,
                            "phone": phone,
                            "updatedAt": last_updated
                        })
                
                if not page_has_recent:
                    whatsapp_logger.info("No recent contacts on this page. Stopping fetch.")
                    break
                
                page += 1
                time.sleep(0.5)  # Rate limiting
                
            except requests.exceptions.RequestException as e:
                whatsapp_logger.error(f"Error fetching contacts page {page}: {e}")
                break
        
        # Keep only the latest contact per phone
        latest_contacts = {}
        for contact in all_contacts:
            phone = contact["phone"]
            if phone not in latest_contacts or (contact["updatedAt"] and contact["updatedAt"] > latest_contacts[phone]["updatedAt"]):
                latest_contacts[phone] = contact
        
        latest_contacts_list = list(latest_contacts.values())
        whatsapp_logger.info(f"Fetched {len(latest_contacts_list)} unique contacts")
        
        return latest_contacts_list
    
    def get_messages_for_contact(self, phone: str, limit: int = 50) -> List[Dict]:
        """Fetch messages for a specific phone number with rate limiting handling"""
        url = f"{self.api_base}/{self.tenant_id}/api/v1/getMessages/{phone}"
        params = {"limit": limit}
        
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                response = requests.get(url, headers=self.headers, params=params, timeout=30)
                
                if response.status_code == 429:  # Rate limited
                    if attempt < max_retries - 1:
                        wait_time = retry_delay * (2 ** attempt)  # Exponential backoff
                        whatsapp_logger.warning(f"Rate limited for {phone}, waiting {wait_time}s before retry {attempt + 1}/{max_retries}")
                        time.sleep(wait_time)
                        continue
                    else:
                        whatsapp_logger.error(f"Rate limit exceeded for {phone} after {max_retries} attempts")
                        return []
                
                response.raise_for_status()
                data = response.json()
                messages = data.get("messages", {}).get("items", [])
                
                return messages
                
            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    whatsapp_logger.warning(f"Error fetching messages for {phone} (attempt {attempt + 1}): {e}")
                    time.sleep(retry_delay)
                    continue
                else:
                    whatsapp_logger.error(f"Failed to fetch messages for {phone} after {max_retries} attempts: {e}")
                    return []
        
        return []


@log_function_call(whatsapp_logger)
def fetch_and_import_wati_data(company_id: str, time_period: str = "24h") -> Dict:
    """
    Fetch WhatsApp data from WATI API and import into database
    
    Args:
        company_id: Company identifier (must have WATI API credentials)
        time_period: Time period to fetch (24h, 7d, 30d)
    
    Returns:
        Dict with success status and statistics
    """
    try:
        # Get company configuration
        company_config = get_company_config(company_id)
        
        if not company_config.has_wati_api():
            return {
                "success": False,
                "error": f"WATI API credentials not configured for {company_config.name}"
            }
        
        # Parse time period
        time_mapping = {
            "24h": 24,
            "7d": 24 * 7,
            "30d": 24 * 30
        }
        
        since_hours = time_mapping.get(time_period, 24)
        since_time = datetime.now(timezone.utc) - timedelta(hours=since_hours)
        
        fetching_logger.info(f"Starting WATI data fetch for {company_config.name} - last {time_period}")
        
        # Initialize WATI client
        client = WATIClient(
            api_token=company_config.wati_api_token,
            tenant_id=company_config.wati_tenant_id,
            api_base=company_config.wati_api_base
        )
        
        # Fetch contacts
        contacts = client.get_contacts(since_hours=since_hours)
        
        if not contacts:
            return {
                "success": True,
                "message": "No recent contacts found",
                "contacts_fetched": 0,
                "messages_imported": 0
            }
        
        # Fetch messages for each contact
        all_messages = []
        wati_events = []  # Full conversation history for pipeline
        processed_contacts = 0
        
        for contact in contacts:
            name = contact.get("name", "").strip()
            phone = contact.get("phone", "").strip()
            
            if not phone:
                continue
            
            processed_contacts += 1
            fetching_logger.info(f"Processing {processed_contacts}/{len(contacts)}: {name} ({phone})")
            
            # Parse phone number
            phone_clean = re.sub(r"\D", "", phone)
            country_code = int(phone_clean[:2]) if len(phone_clean) > 10 else 92
            contact_number = int(phone_clean[-10:]) if len(phone_clean) >= 10 else None
            
            if not contact_number:
                whatsapp_logger.warning(f"Invalid phone number format: {phone}")
                continue
            
            # Fetch messages with rate limiting handling
            messages = client.get_messages_for_contact(phone, limit=200)  # Get more messages for full context
            
            for message in messages:
                if message.get("type") == "text":
                    timestamp_str = message.get("created", "")
                    try:
                        timestamp_dt = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                        if timestamp_dt.tzinfo is None:
                            timestamp_dt = timestamp_dt.replace(tzinfo=timezone.utc)
                    except Exception as e:
                        whatsapp_logger.warning(f"Failed to parse timestamp {timestamp_str}: {e}")
                        continue
                    
                    text = message.get("text", "")
                    
                    # Add to full WATI events for pipeline (all messages for context)
                    wati_event = message.copy()
                    wati_event["whatsappPhoneNumber"] = phone
                    wati_event["eventType"] = "message"
                    wati_events.append(wati_event)
                    
                    # Only include messages from the specified time period for database
                    if timestamp_dt >= since_time:
                        # Classify message type using the same logic as original app
                        msg_type = classify_whatsapp_message(text)
                        
                        formatted_message = {
                            "CustomerName": name,
                            "CountryCode": country_code,
                            "ContactNumber": contact_number,
                            "MessageType": msg_type,
                            "Message": text,
                            "Timestamp": timestamp_str
                        }
                        all_messages.append(formatted_message)
            
            # Rate limiting between contacts
            time.sleep(0.8)  # Increased delay to avoid rate limits
        
        # Save messages to database
        imported_count = 0
        skipped_count = 0
        
        for msg_data in all_messages:
            try:
                # Check if message already exists
                existing = WhatsAppMessage.get_by_content_and_timestamp(
                    msg_data["Message"], 
                    msg_data["Timestamp"]
                )
                
                if existing:
                    skipped_count += 1
                    continue
                
                # Create new message
                message = WhatsAppMessage.create(
                    customer_name=msg_data["CustomerName"],
                    country_code=msg_data["CountryCode"],
                    contact_number=msg_data["ContactNumber"],
                    message_type=msg_data["MessageType"],
                    message=msg_data["Message"],
                    timestamp=msg_data["Timestamp"],
                    company_id=company_id
                )
                
                if message:
                    imported_count += 1
                
            except Exception as e:
                whatsapp_logger.error(f"Error importing message: {e}")
                skipped_count += 1
        
        # Save raw data to JSON file for backup (simplified format)
        json_filename = f"data/WATI_Messages_{company_id}_{time_period}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        try:
            with open(json_filename, "w", encoding="utf-8") as f:
                json.dump(all_messages, f, indent=2, ensure_ascii=False)
            whatsapp_logger.info(f"Raw data saved to {json_filename}")
        except Exception as e:
            whatsapp_logger.warning(f"Failed to save raw data: {e}")
        
        # Save WATI events for pipeline processing (full conversation format)
        wati_filename = f"data/WATI_Full_Conversations_{company_id}_{time_period}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        try:
            with open(wati_filename, "w", encoding="utf-8") as f:
                json.dump(wati_events, f, indent=2, ensure_ascii=False)
            whatsapp_logger.info(f"WATI events saved to {wati_filename}")
        except Exception as e:
            whatsapp_logger.warning(f"Failed to save WATI events: {e}")
            wati_filename = json_filename  # Fallback to simplified format
        
        result = {
            "success": True,
            "message": f"WATI data fetch completed for {company_config.name}",
            "contacts_fetched": len(contacts),
            "messages_found": len(all_messages),
            "messages_imported": imported_count,
            "messages_skipped": skipped_count,
            "time_period": time_period,
            "json_file": json_filename,
            "wati_file": wati_filename
        }
        
        whatsapp_logger.info(f"WATI import completed: {result}")
        
        # Start pipeline processing for WhatsApp data if we imported new messages
        should_run_pipeline = imported_count > 0
        
        # Also check if this is first time setup (no existing WhatsApp data)
        try:
            from ai.haval_pipeline import get_pipeline_status
            status = get_pipeline_status()
            if not status.get("whatsapp_blocks", 0):
                should_run_pipeline = True
                whatsapp_logger.info("WhatsApp vector DB appears empty, running pipeline for initial setup")
        except Exception as e:
            whatsapp_logger.warning(f"Could not check pipeline status: {e}")
            should_run_pipeline = True  # Run pipeline to be safe
        
        if should_run_pipeline:
            try:
                from ai.haval_pipeline import start_haval_pipeline
                
                # Start pipeline with WATI events file (full conversation format)
                start_haval_pipeline(
                    json_path=wati_filename,
                    topic_url="whatsapp://wati_conversations",
                    sources="Whatsapp",  # Use capital W for Whatsapp
                    company_id=company_id
                )
                
                whatsapp_logger.info(f"Started AI pipeline processing for {len(wati_events)} WATI events")
                result["pipeline_started"] = True
                
            except Exception as e:
                whatsapp_logger.warning(f"WATI import completed but pipeline startup failed: {str(e)}")
                result["pipeline_error"] = str(e)
        else:
            whatsapp_logger.info("No new messages imported, skipping pipeline processing")
            result["pipeline_skipped"] = "No new messages"
        
        return result
        
    except Exception as e:
        error_msg = f"Error during WATI data fetch: {str(e)}"
        log_error(e, "WATI data fetch failed")
        return {
            "success": False,
            "error": error_msg
        }


def get_wati_status(company_id: str) -> Dict:
    """Get WATI API status for a company"""
    try:
        company_config = get_company_config(company_id)
        
        if not company_config.has_wati_api():
            return {
                "available": False,
                "error": "WATI API credentials not configured"
            }
        
        # Test API connection
        client = WATIClient(
            api_token=company_config.wati_api_token,
            tenant_id=company_config.wati_tenant_id,
            api_base=company_config.wati_api_base
        )
        
        # Try to fetch a small number of contacts to test connection
        url = f"{client.api_base}/{client.tenant_id}/api/v1/getContacts"
        params = {"pageNumber": 1, "pageSize": 1}
        
        response = requests.get(url, headers=client.headers, params=params, timeout=10)
        
        if response.status_code == 200:
            return {
                "available": True,
                "status": "connected",
                "api_base": company_config.wati_api_base,
                "tenant_id": company_config.wati_tenant_id
            }
        else:
            return {
                "available": False,
                "error": f"API connection failed: {response.status_code}",
                "status_code": response.status_code
            }
            
    except Exception as e:
        return {
            "available": False,
            "error": f"Connection test failed: {str(e)}"
        }