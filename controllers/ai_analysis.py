"""
AI Analysis Controller - Handles intelligent query analysis and user-specific insights
"""

import re
import json
from typing import Optional, List, Dict
from flask import jsonify, request
from flask_login import login_required, current_user
from models import get_db_connection
from utils.logger import log_function_call, ai_logger


@log_function_call(ai_logger)
def extract_structured_data(answer: str, platform_data: Optional[List[Dict]], mode: str) -> Dict:
    """
    Extract structured data from chatbot answer including:
    - References (WhatsApp messages, PakWheels posts with username, timestamp)
    - Charts (already in markdown format)
    - Recommendations/suggestions
    - Tables
    """
    from datetime import datetime
    
    structured = {
        "references": [],
        "charts": [],
        "tables": [],
        "recommendations": [],
        "followups": []  # Add followups field
    }
    
    # Extract references directly from RAG engine citation format
    # Pattern: **[1]** 👤 username | 📅 date | 🔗 source [| 📞 phone]
    #          💬 *"snippet"*
    #          🔗 [View Source](url)
    
    # Use a more robust approach to parse citations
    citations = []
    
    if "📋 References" in answer:
        # Find the references section
        ref_start = answer.find("📋 References")
        ref_section = answer[ref_start:]
        
        # Split into individual citation blocks
        citation_blocks = re.split(r'\*\*\[(\d+)\]\*\*', ref_section)[1:]  # Skip first empty part
        
        # Process pairs: [number, content]
        for i in range(0, len(citation_blocks), 2):
            if i + 1 < len(citation_blocks):
                ref_num = citation_blocks[i]
                content = citation_blocks[i + 1]
                
                # Parse the content for metadata
                lines = content.strip().split('\n')
                if len(lines) >= 2:
                    # First line: 👤 username | 📅 date | 🔗 source [| 📞 phone]
                    header_line = lines[0].strip()
                    
                    # Extract username, date, source, phone
                    parts = [p.strip() for p in header_line.split('|')]
                    username = parts[0].replace('👤', '').strip() if len(parts) > 0 else 'Unknown'
                    date = parts[1].replace('📅', '').strip() if len(parts) > 1 else 'N/A'
                    source = parts[2].replace('🔗', '').strip() if len(parts) > 2 else 'Unknown'
                    phone = parts[3].replace('📞', '').strip() if len(parts) > 3 else ''
                    
                    # Second line: 💬 *"message"*
                    message_line = lines[1].strip() if len(lines) > 1 else ''
                    message = re.sub(r'💬\s*\*"([^"]+)"\*', r'\1', message_line)
                    
                    # Third line (optional): 🔗 [View Source](url)
                    url = ''
                    if len(lines) > 2:
                        url_match = re.search(r'🔗\s*\[View Source\]\(([^)]+)\)', lines[2])
                        if url_match:
                            url = url_match.group(1)
                    
                    citations.append((ref_num, username, date, source, phone, message, url))
    
    ai_logger.debug(f"Found {len(citations)} citations using robust parsing")
    
    for citation in citations:
        ref_num, username, date, source, phone, snippet, url = citation
        ai_logger.debug(f"Processing citation {ref_num}: source='{source}', phone='{phone}', url='{url}'")
        
        # Determine reference type based on source
        if "WhatsApp" in source:
            # For WhatsApp references, only include phone number if it's valid
            phone_number = phone.strip() if phone and phone.strip() and phone.strip() != "N/A" else None
            ref_data = {
                "type": "whatsapp",
                "id": f"WA-{ref_num}",
                "number": int(ref_num),
                "username": username.strip(),
                "timestamp": date.strip(),
                "message": snippet.strip(),
                "message_type": "Message"
            }
            # Only add phone fields if we have a valid phone number
            if phone_number:
                ref_data["contact"] = phone_number
                ref_data["phone_number"] = phone_number
            structured["references"].append(ref_data)
        else:
            # PakWheels reference
            # Extract post number from URL if available
            post_number = None
            post_url = url.strip() if url else None
            
            if post_url:
                # Try to extract post number from URL
                post_number_match = re.search(r'/(\d+)/?$', post_url)
                if post_number_match:
                    post_number = post_number_match.group(1)
            
            # If no post number found, construct URL using reference number as fallback
            if not post_url or not post_number:
                post_number = ref_num  # Use reference number as fallback
                post_url = f"https://www.pakwheels.com/forums/t/haval-h6-dedicated-discussion-owner-fan-club-thread/2198325/{post_number}"
            
            ai_logger.debug(f"PakWheels reference {ref_num}: post_number={post_number}, url={post_url}")
            
            structured["references"].append({
                "type": "pakwheels",
                "number": int(ref_num),
                "id": post_number,
                "username": username.strip(),
                "date": date.strip(),
                "message": snippet.strip(),
                "url": post_url,
                "post_number": post_number
            })
    
    # Extract chart definitions from markdown code blocks
    chart_pattern = r'```chart\s*\n([\s\S]*?)```'
    charts = re.findall(chart_pattern, answer)
    for chart_code in charts:
        try:
            lines = chart_code.strip().split('\n')
            chart_data = {}
            chart_type = 'bar'
            chart_title = 'Chart'
            
            for line in lines:
                line = line.strip()
                if line.startswith('type:'):
                    chart_type = line.split(':', 1)[1].strip()
                elif line.startswith('title:'):
                    chart_title = line.split(':', 1)[1].strip()
                elif line.startswith('data:'):
                    data_str = line.split(':', 1)[1].strip()
                    chart_data = json.loads(data_str)
            
            if chart_data:
                structured["charts"].append({
                    "type": chart_type,
                    "title": chart_title,
                    "data": chart_data
                })
        except Exception:
            continue
    
    # Extract tables from markdown
    table_pattern = r'\|(.+)\|\n\|[-\s|]+\|\n((?:\|.+\|\n?)+)'
    tables = re.findall(table_pattern, answer)
    for header, rows in tables:
        try:
            headers = [h.strip() for h in header.split('|') if h.strip()]
            table_rows = []
            for row in rows.strip().split('\n'):
                if row.strip():
                    cells = [c.strip() for c in row.split('|') if c.strip()]
                    if len(cells) == len(headers):
                        table_rows.append(cells)
            
            if headers and table_rows:
                structured["tables"].append({
                    "headers": headers,
                    "rows": table_rows
                })
        except Exception:
            continue
    
    # Extract recommendations section
    rec_pattern = r'(?:###?\s*)?(?:💡\s*)?(?:Recommendations?|Suggestions?|Action Items?)[:\s]*\n((?:[-*•]\s*.+\n?)+)'
    rec_match = re.search(rec_pattern, answer, re.IGNORECASE | re.MULTILINE)
    if rec_match:
        rec_text = rec_match.group(1)
        recommendations = [r.strip().lstrip('-*• ') for r in rec_text.split('\n') if r.strip()]
        structured["recommendations"] = recommendations
    else:
        # If no explicit recommendations section found, generate some based on the content
        if any(word in answer.lower() for word in ['problem', 'issue', 'concern', 'fault']):
            structured["recommendations"] = [
                "Consider researching these specific issues before making a decision",
                "Check warranty coverage for common problems mentioned",
                "Test drive thoroughly to verify performance",
                "Consult with authorized service centers for maintenance requirements"
            ]
    
    # Always generate follow-up questions based on the original query (not just when there are recommendations)
    followup_questions = generate_followup_questions(structured.get("recommendations", []), answer)
    structured["followups"] = followup_questions
    
    return structured


def generate_followup_questions(recommendations, answer_text):
    """Generate specific, clickable questions about problems and issues"""
    followup_questions = []
    
    # Analyze the answer text to understand context
    answer_lower = answer_text.lower()
    
    # Car-related problem questions
    car_brands = ['haval', 'jolion', 'h6', 'toyota', 'honda', 'suzuki', 'civic', 'corolla', 'city', 'cultus']
    detected_car = None
    for car in car_brands:
        if car in answer_lower:
            detected_car = car
            break
    
    if detected_car:
        # Specific car problem questions
        followup_questions.extend([
            f"What are the top 10 most common problems with {detected_car.title()}?",
            f"Show me engine-related issues reported for {detected_car.title()}",
            f"What electrical problems do {detected_car.title()} owners face?",
            f"List transmission issues in {detected_car.title()}",
            f"What are the most expensive repairs needed for {detected_car.title()}?",
            f"Show me brake system problems in {detected_car.title()}"
        ])
    
    # Service and delivery problem questions
    if any(word in answer_lower for word in ['delivery', 'service', 'dealership', 'booking']):
        followup_questions.extend([
            "What are the most common delivery delay problems?",
            "Show me top 10 service center complaints",
            "What booking system issues do customers face?",
            "List the most reported dealership problems",
            "What are the worst service experiences customers have shared?",
            "Show me delivery timeline problems by city"
        ])
    
    # Technical problem questions
    if any(word in answer_lower for word in ['problem', 'issue', 'fault', 'error', 'trouble']):
        followup_questions.extend([
            "What are the top 15 technical problems customers report?",
            "Show me the most critical safety issues reported",
            "List software/infotainment problems customers face",
            "What are the most frequent warranty claim issues?",
            "Show me air conditioning and heating problems",
            "What paint and body issues do customers report?"
        ])
    
    # Price and financing problem questions
    if any(word in answer_lower for word in ['price', 'cost', 'finance', 'loan', 'installment', 'payment']):
        followup_questions.extend([
            "What are the hidden costs customers complain about?",
            "Show me financing approval problems customers face",
            "What payment processing issues are most common?",
            "List insurance-related problems customers report",
            "What are the most complained about additional charges?",
            "Show me loan documentation problems"
        ])
    
    # Quality and manufacturing problem questions
    if any(word in answer_lower for word in ['quality', 'manufacturing', 'defect', 'recall']):
        followup_questions.extend([
            "What are the top 20 manufacturing defects reported?",
            "Show me quality control issues by model year",
            "List the most common paint and finish problems",
            "What interior quality issues do customers report?",
            "Show me engine manufacturing problems",
            "What safety recalls have been issued?"
        ])
    
    # Customer service problem questions
    if any(word in answer_lower for word in ['customer', 'service', 'support', 'staff']):
        followup_questions.extend([
            "What are the worst customer service experiences shared?",
            "Show me top 10 staff behavior complaints",
            "List communication problems customers face",
            "What are the most frustrating service center issues?",
            "Show me response time problems customers report",
            "What training gaps do customers notice in staff?"
        ])
    
    # Parts and maintenance problem questions
    if any(word in answer_lower for word in ['parts', 'maintenance', 'repair', 'spare']):
        followup_questions.extend([
            "What are the most expensive parts that fail frequently?",
            "Show me parts availability problems by region",
            "List the most common maintenance issues under 50,000km",
            "What are the hardest parts to find for repairs?",
            "Show me overpriced parts customers complain about",
            "What maintenance schedule problems do customers face?"
        ])
    
    # General top problems if no specific context
    if not followup_questions:
        followup_questions = [
            "What are the top 25 problems customers report overall?",
            "Show me the most critical issues that need immediate attention",
            "List problems that affect customer satisfaction the most",
            "What are the most expensive problems customers face?",
            "Show me problems that cause customers to regret their purchase",
            "What issues make customers switch to competitors?",
            "List problems that take the longest time to resolve",
            "What are the most frustrating recurring problems?",
            "Show me problems that void warranty coverage",
            "What safety-related problems are most concerning?"
        ]
    
    # Ensure questions are unique and limit to 6
    unique_questions = list(dict.fromkeys(followup_questions))
    return unique_questions[:6]


@log_function_call(ai_logger)
def ai_analyze_query(query, cur):
    """AI-powered query analysis with intelligent responses"""
    query_lower = query.lower()
    
    # Detect car brands/models in query
    car_keywords = {
        'haval': ['haval', 'h6', 'jolion'],
        'toyota': ['toyota', 'corolla', 'yaris', 'vitz', 'prado', 'fortuner'],
        'honda': ['honda', 'civic', 'city', 'accord', 'brv', 'hrv'],
        'suzuki': ['suzuki', 'cultus', 'mehran', 'alto', 'swift', 'wagon r'],
        'kia': ['kia', 'sportage', 'picanto', 'sorento', 'stonic'],
        'hyundai': ['hyundai', 'tucson', 'elantra', 'sonata', 'santa fe'],
        'mg': ['mg', 'hs', 'zs', 'mg5'],
        'changan': ['changan', 'oshan', 'alsvin', 'karvaan']
    }
    
    detected_car = None
    for brand, keywords in car_keywords.items():
        for keyword in keywords:
            if keyword in query_lower:
                detected_car = brand
                break
        if detected_car:
            break
    
    # Car-specific review/opinion queries
    if detected_car and any(word in query_lower for word in ['review', 'opinion', 'good', 'bad', 'worth', 'buy', 'recommend', 'experience', 'feedback', 'thoughts']):
        return generate_car_review(detected_car, cur)
    
    # Problem/issue queries
    if any(word in query_lower for word in ['problem', 'issue', 'fault', 'defect', 'complaint', 'trouble', 'error', 'not working', 'broken']):
        if detected_car:
            return analyze_car_problems(detected_car, cur)
        else:
            return analyze_general_problems(query_lower, cur)
    
    # Comparison queries
    if 'vs' in query_lower or 'versus' in query_lower or 'compare' in query_lower or 'better' in query_lower:
        return handle_comparison_query(query_lower, cur)
    
    # Fuel average queries
    if any(word in query_lower for word in ['fuel', 'mileage', 'average', 'consumption', 'petrol', 'diesel']):
        if detected_car:
            return analyze_fuel_average(detected_car, cur)
        else:
            return analyze_general_fuel(query_lower, cur)
    
    # Price queries
    if any(word in query_lower for word in ['price', 'cost', 'expensive', 'cheap', 'worth', 'value']):
        if detected_car:
            return analyze_car_pricing(detected_car, cur)
    
    # Features queries
    if any(word in query_lower for word in ['feature', 'specification', 'spec', 'equipment', 'technology']):
        if detected_car:
            return analyze_car_features(detected_car, cur)
    
    # Statistics queries
    if "how many" in query_lower or "count" in query_lower or "total" in query_lower:
        return handle_statistics_query(query_lower, cur)
    
    # Top/best queries
    if "top" in query_lower or "best" in query_lower or "popular" in query_lower:
        return handle_top_query(query_lower, cur)
    
    # User-specific queries (this is what was missing!)
    if any(word in query_lower for word in ['user', 'customer', 'owner', 'member']):
        return analyze_user_discussions(query, cur)
    
    # General search
    if detected_car:
        return search_car_discussions(detected_car, cur)
    
    # Fallback: intelligent keyword search
    return intelligent_search(query, cur)


@log_function_call(ai_logger)
def generate_car_review(car_brand, cur):
    """Generate AI-powered car review from user feedback"""
    # Search both tables for car mentions
    cur.execute("""
        SELECT cooked_text FROM posts 
        WHERE LOWER(topic_title) LIKE ? OR LOWER(cooked_text) LIKE ?
        LIMIT 50
    """, (f"%{car_brand}%", f"%{car_brand}%"))
    posts = [row[0] for row in cur.fetchall()]
    
    cur.execute("""
        SELECT post_text FROM search_results 
        WHERE LOWER(topic_title) LIKE ? OR LOWER(post_text) LIKE ?
        LIMIT 50
    """, (f"%{car_brand}%", f"%{car_brand}%"))
    posts.extend([row[0] for row in cur.fetchall()])
    
    if not posts:
        return f"I don't have enough data about {car_brand.title()} yet. Try searching for it first!"
    
    # Analyze sentiment and extract key points
    positive_words = ['good', 'great', 'excellent', 'amazing', 'love', 'best', 'perfect', 'recommend', 'happy', 'satisfied']
    negative_words = ['bad', 'poor', 'worst', 'hate', 'terrible', 'awful', 'disappointed', 'regret', 'problem', 'issue']
    
    positive_count = 0
    negative_count = 0
    total_posts = len(posts)
    
    # Extract common topics
    fuel_mentions = []
    price_mentions = []
    feature_mentions = []
    problem_mentions = []
    
    for post in posts:
        post_lower = post.lower()
        
        # Sentiment analysis
        for word in positive_words:
            if word in post_lower:
                positive_count += 1
        for word in negative_words:
            if word in post_lower:
                negative_count += 1
        
        # Extract specific mentions
        if any(word in post_lower for word in ['fuel', 'mileage', 'average']):
            fuel_mentions.append(post[:200])
        if any(word in post_lower for word in ['price', 'cost', 'expensive']):
            price_mentions.append(post[:200])
        if any(word in post_lower for word in ['feature', 'technology', 'equipment']):
            feature_mentions.append(post[:200])
        if any(word in post_lower for word in ['problem', 'issue', 'fault']):
            problem_mentions.append(post[:200])
    
    # Generate review
    sentiment = "POSITIVE" if positive_count > negative_count else "MIXED" if positive_count == negative_count else "NEGATIVE"
    sentiment_emoji = "😊" if sentiment == "POSITIVE" else "😐" if sentiment == "MIXED" else "😟"
    
    review = f"🚗 **{car_brand.upper()} - User Review Summary** {sentiment_emoji}\n\n"
    review += f"📊 **Analysis based on {total_posts} user posts**\n\n"
    review += f"**Overall Sentiment:** {sentiment}\n"
    review += f"• Positive mentions: {positive_count}\n"
    review += f"• Negative mentions: {negative_count}\n\n"
    
    if fuel_mentions:
        review += f"⛽ **Fuel Economy:**\n"
        review += f"Users discussed fuel average in {len(fuel_mentions)} posts. "
        review += "Generally, users mention fuel consumption and mileage concerns.\n\n"
    
    if price_mentions:
        review += f"💰 **Pricing:**\n"
        review += f"Price discussed in {len(price_mentions)} posts. "
        review += "Users have varying opinions on value for money.\n\n"
    
    if feature_mentions:
        review += f"✨ **Features:**\n"
        review += f"Features mentioned in {len(feature_mentions)} posts. "
        review += "Users discuss technology and equipment levels.\n\n"
    
    if problem_mentions:
        review += f"⚠️ **Common Issues:**\n"
        review += f"Problems reported in {len(problem_mentions)} posts. "
        review += "Some users have experienced issues worth noting.\n\n"
    
    review += f"💡 **Recommendation:**\n"
    if sentiment == "POSITIVE":
        review += f"Based on user feedback, {car_brand.title()} seems to be well-received by owners. "
        review += "Most users report positive experiences."
    elif sentiment == "MIXED":
        review += f"User opinions on {car_brand.title()} are mixed. "
        review += "Consider researching specific aspects that matter to you."
    else:
        review += f"User feedback for {car_brand.title()} shows some concerns. "
        review += "Review common issues before making a decision."
    
    return review


@log_function_call(ai_logger)
def analyze_car_problems(car_brand, cur):
    """Analyze common problems for a specific car"""
    problem_keywords = ['problem', 'issue', 'fault', 'defect', 'not working', 'broken', 'repair', 'fix', 'complaint', 'malfunction']
    
    # Search in both tables
    problems = []
    
    # From posts table
    for keyword in problem_keywords:
        cur.execute("""
            SELECT topic_title, cooked_text, author, 'posts' as source FROM posts 
            WHERE (LOWER(topic_title) LIKE ? OR LOWER(cooked_text) LIKE ?)
            AND LOWER(cooked_text) LIKE ?
            LIMIT 5
        """, (f"%{car_brand}%", f"%{car_brand}%", f"%{keyword}%"))
        problems.extend(cur.fetchall())
    
    # From search_results table
    for keyword in problem_keywords:
        cur.execute("""
            SELECT topic_title, post_text, author, 'search' as source FROM search_results 
            WHERE (LOWER(topic_title) LIKE ? OR LOWER(post_text) LIKE ?)
            AND LOWER(post_text) LIKE ?
            LIMIT 5
        """, (f"%{car_brand}%", f"%{car_brand}%", f"%{keyword}%"))
        problems.extend(cur.fetchall())
    
    # Remove duplicates
    unique_problems = []
    seen_texts = set()
    for problem in problems:
        text_snippet = problem[1][:100]
        if text_snippet not in seen_texts:
            seen_texts.add(text_snippet)
            unique_problems.append(problem)
    
    if not unique_problems:
        return f"✅ **Good news!** I couldn't find many reported problems for {car_brand.title()} in the database.\n\nThis could mean:\n• The car is generally reliable\n• Users haven't reported major issues\n• Limited data available\n\nAlways research and test drive before buying!"
    
    response = f"⚠️ **COMMON ISSUES WITH {car_brand.upper()}**\n\n"
    response += f"Found {len(unique_problems)} posts discussing problems:\n\n"
    
    # Categorize problems
    categories = {
        'Engine': ['engine', 'motor', 'power', 'acceleration', 'turbo', 'oil', 'overheating'],
        'Transmission': ['transmission', 'gear', 'shifting', 'clutch', 'cvt'],
        'Electrical': ['electrical', 'battery', 'light', 'sensor', 'electronics', 'wiring'],
        'AC/Cooling': ['ac', 'air conditioning', 'cooling', 'heater', 'climate', 'compressor'],
        'Suspension': ['suspension', 'shock', 'ride', 'noise', 'vibration', 'steering'],
        'Brakes': ['brake', 'braking', 'abs', 'pad'],
        'Body/Interior': ['paint', 'rust', 'interior', 'seat', 'door', 'window', 'trim'],
        'Fuel System': ['fuel', 'pump', 'injector', 'consumption', 'tank'],
        'Other': []
    }
    
    categorized = {cat: [] for cat in categories}
    
    for title, text, author, source in unique_problems[:30]:
        text_lower = text.lower()
        categorized_flag = False
        for category, keywords in categories.items():
            if category != 'Other' and any(kw in text_lower for kw in keywords):
                categorized[category].append((title, text[:200], author, source))
                categorized_flag = True
                break
        if not categorized_flag:
            categorized['Other'].append((title, text[:200], author, source))
    
    # Display categorized problems
    total_shown = 0
    for category, items in categorized.items():
        if items:
            response += f"\n**{category} Issues ({len(items)}):**\n"
            for i, (title, text, author, source) in enumerate(items[:4], 1):  # Show top 4 per category
                source_badge = "🔍" if source == "search" else "📁"
                response += f"{i}. {text}...\n   {source_badge} By: {author}\n\n"
                total_shown += 1
    
    if len(unique_problems) > total_shown:
        response += f"... and {len(unique_problems) - total_shown} more issues reported.\n\n"
    
    response += "💡 **Recommendation:**\n"
    response += "• Research these specific issues before buying\n"
    response += "• Ask about warranty coverage for common problems\n"
    response += "• Test drive thoroughly\n"
    response += "• Check service history if buying used\n"
    
    return response


@log_function_call(ai_logger)
def analyze_user_discussions(query, cur):
    """Analyze discussions by specific users or about users - THIS WAS THE MISSING FUNCTIONALITY!"""
    # Extract potential usernames from query
    words = query.split()
    potential_users = [w for w in words if len(w) > 2 and not w.lower() in ['user', 'customer', 'owner', 'member', 'about', 'from', 'by']]
    
    if not potential_users:
        return "Please specify a username or user-related query (e.g., 'show posts by john', 'what did sarah say about haval')"
    
    search_term = potential_users[0]
    
    # Search for posts by this user (author field)
    cur.execute("""
        SELECT topic_title, cooked_text, author, created_at FROM posts 
        WHERE LOWER(author) LIKE ?
        ORDER BY created_at DESC
        LIMIT 20
    """, (f"%{search_term.lower()}%",))
    user_posts = cur.fetchall()
    
    # Also search for mentions of this user in content
    cur.execute("""
        SELECT topic_title, cooked_text, author, created_at FROM posts 
        WHERE LOWER(cooked_text) LIKE ? AND LOWER(author) != ?
        ORDER BY created_at DESC
        LIMIT 10
    """, (f"%{search_term.lower()}%", f"%{search_term.lower()}%"))
    mentions = cur.fetchall()
    
    # Search WhatsApp messages if available
    whatsapp_messages = []
    try:
        # First try exact match (like old project)
        cur.execute("""
            SELECT customer_name, message, timestamp, message_type FROM whatsapp_messages 
            WHERE customer_name = ?
            ORDER BY timestamp DESC
            LIMIT 10
        """, (search_term,))
        whatsapp_messages = cur.fetchall()
        
        # If no exact match, try partial match (case-insensitive)
        if not whatsapp_messages:
            cur.execute("""
                SELECT customer_name, message, timestamp, message_type FROM whatsapp_messages 
                WHERE LOWER(customer_name) LIKE ?
                ORDER BY timestamp DESC
                LIMIT 10
            """, (f"%{search_term.lower()}%",))
            whatsapp_messages = cur.fetchall()
            
        # If still no match, try with URL decoding (for names with special characters)
        if not whatsapp_messages:
            import urllib.parse
            decoded_search = urllib.parse.unquote(search_term)
            if decoded_search != search_term:
                cur.execute("""
                    SELECT customer_name, message, timestamp, message_type FROM whatsapp_messages 
                    WHERE customer_name = ? OR LOWER(customer_name) LIKE ?
                    ORDER BY timestamp DESC
                    LIMIT 10
                """, (decoded_search, f"%{decoded_search.lower()}%"))
                whatsapp_messages = cur.fetchall()
    except Exception as e:
        ai_logger.warning(f"Error searching WhatsApp messages: {e}")
        pass  # WhatsApp table might not exist
    
    if not user_posts and not mentions and not whatsapp_messages:
        # Enhanced error message with debugging info
        debug_info = ""
        try:
            # Check if WhatsApp table exists and has data
            cur.execute("SELECT COUNT(*) FROM whatsapp_messages")
            total_whatsapp = cur.fetchone()[0]
            
            # Get some sample customer names for suggestions
            cur.execute("SELECT DISTINCT customer_name FROM whatsapp_messages LIMIT 10")
            sample_customers = [row[0] for row in cur.fetchall()]
            
            debug_info = f"\n\n**Database Info:**\n• Total WhatsApp messages: {total_whatsapp}\n• Sample customer names: {', '.join(sample_customers[:5])}"
            if len(sample_customers) > 5:
                debug_info += f" (and {len(sample_customers) - 5} more)"
                
        except Exception as e:
            debug_info = f"\n\n**Database Status:** WhatsApp table may not exist or be empty ({str(e)})"
        
        return f"❌ **No discussions found for '{search_term}'**\n\nI couldn't find any posts, messages, or mentions of '{search_term}' in the database.{debug_info}\n\n💡 **Suggestions:**\n• Check the spelling (try exact spelling)\n• Try a shorter version of the name\n• Make sure the user has posted in the forums or sent WhatsApp messages\n• Try searching for their posts about specific topics\n• Check the customer list in the WhatsApp view"
    
    response = f"👤 **User Analysis: '{search_term}'**\n\n"
    
    # Posts by this user
    if user_posts:
        response += f"📝 **Posts by {search_term} ({len(user_posts)}):**\n\n"
        for i, (title, text, author, date) in enumerate(user_posts[:5], 1):
            response += f"{i}. **{title}**\n"
            response += f"   📅 {date}\n"
            response += f"   💬 {text[:150]}...\n\n"
        
        if len(user_posts) > 5:
            response += f"... and {len(user_posts) - 5} more posts by {search_term}\n\n"
    
    # Mentions of this user
    if mentions:
        response += f"🗣️ **Mentions of {search_term} ({len(mentions)}):**\n\n"
        for i, (title, text, author, date) in enumerate(mentions[:3], 1):
            response += f"{i}. **{title}** (by {author})\n"
            response += f"   📅 {date}\n"
            response += f"   💬 {text[:150]}...\n\n"
    
    # WhatsApp messages
    if whatsapp_messages:
        response += f"📱 **WhatsApp Messages from {search_term} ({len(whatsapp_messages)}):**\n\n"
        for i, (name, message, timestamp, msg_type) in enumerate(whatsapp_messages[:3], 1):
            type_emoji = "❓" if msg_type == "query" else "⚠️" if msg_type == "complaint" else "💬"
            response += f"{i}. {type_emoji} **{msg_type.title()}** ({timestamp})\n"
            response += f"   💬 {message[:150]}...\n\n"
    
    # Analysis summary
    total_interactions = len(user_posts) + len(mentions) + len(whatsapp_messages)
    response += f"📊 **Summary:**\n"
    response += f"• Total interactions found: {total_interactions}\n"
    response += f"• Forum posts: {len(user_posts)}\n"
    response += f"• Mentions by others: {len(mentions)}\n"
    response += f"• WhatsApp messages: {len(whatsapp_messages)}\n\n"
    
    if user_posts:
        # Analyze sentiment of user's posts
        all_text = " ".join([post[1] for post in user_posts])
        positive_words = ['good', 'great', 'excellent', 'love', 'best', 'perfect', 'recommend', 'happy', 'satisfied']
        negative_words = ['bad', 'poor', 'worst', 'hate', 'terrible', 'problem', 'issue', 'disappointed']
        
        pos_count = sum(1 for word in positive_words if word in all_text.lower())
        neg_count = sum(1 for word in negative_words if word in all_text.lower())
        
        if pos_count > neg_count:
            response += f"😊 **User Sentiment:** Generally positive ({pos_count} positive vs {neg_count} negative indicators)\n"
        elif neg_count > pos_count:
            response += f"😟 **User Sentiment:** Some concerns expressed ({neg_count} negative vs {pos_count} positive indicators)\n"
        else:
            response += f"😐 **User Sentiment:** Neutral/Mixed feedback\n"
    
    return response


@log_function_call(ai_logger)
def analyze_general_problems(query, cur):
    """Analyze general problems mentioned in query"""
    # Extract problem keywords from query
    words = query.split()
    search_terms = [w for w in words if len(w) > 3 and w not in ['problem', 'issue', 'with', 'about', 'have']]
    
    if not search_terms:
        return "Please specify what problem you're asking about (e.g., 'engine problem', 'AC issue')."
    
    search_term = search_terms[0]
    
    cur.execute("""
        SELECT topic_title, cooked_text, author FROM posts 
        WHERE LOWER(cooked_text) LIKE ?
        LIMIT 10
    """, (f"%{search_term}%",))
    results = cur.fetchall()
    
    if not results:
        return f"I couldn't find discussions about '{search_term}' problems in the database."
    
    response = f"🔍 **Problems related to '{search_term}':**\n\n"
    response += f"Found {len(results)} relevant discussions:\n\n"
    
    for i, (title, text, author) in enumerate(results[:5], 1):
        response += f"{i}. **{title}**\n"
        response += f"   {text[:200]}...\n"
        response += f"   (Posted by: {author})\n\n"
    
    return response


@log_function_call(ai_logger)
def handle_comparison_query(query, cur):
    """Handle car comparison queries"""
    # Extract car names from query
    car_keywords = ['haval', 'toyota', 'honda', 'suzuki', 'kia', 'hyundai', 'mg', 'changan',
                    'corolla', 'civic', 'city', 'cultus', 'sportage', 'tucson', 'jolion', 'h6']
    
    found_cars = [car for car in car_keywords if car in query]
    
    if len(found_cars) < 2:
        return "Please specify two cars to compare (e.g., 'Compare Haval H6 vs Kia Sportage')."
    
    car1, car2 = found_cars[0], found_cars[1]
    
    # Get post counts for each
    cur.execute("SELECT COUNT(*) FROM posts WHERE LOWER(topic_title) LIKE ? OR LOWER(cooked_text) LIKE ?", 
                (f"%{car1}%", f"%{car1}%"))
    car1_count = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM posts WHERE LOWER(topic_title) LIKE ? OR LOWER(cooked_text) LIKE ?", 
                (f"%{car2}%", f"%{car2}%"))
    car2_count = cur.fetchone()[0]
    
    response = f"🔄 **Comparison: {car1.upper()} vs {car2.upper()}**\n\n"
    response += f"📊 **Discussion Volume:**\n"
    response += f"• {car1.title()}: {car1_count} posts\n"
    response += f"• {car2.title()}: {car2_count} posts\n\n"
    
    if car1_count > car2_count:
        response += f"💬 {car1.title()} has more discussions, suggesting higher popularity or more user experiences.\n\n"
    elif car2_count > car1_count:
        response += f"💬 {car2.title()} has more discussions, suggesting higher popularity or more user experiences.\n\n"
    
    # Get sample opinions
    cur.execute("""
        SELECT cooked_text FROM posts 
        WHERE (LOWER(topic_title) LIKE ? OR LOWER(cooked_text) LIKE ?)
        AND (LOWER(cooked_text) LIKE ? OR LOWER(cooked_text) LIKE ?)
        LIMIT 3
    """, (f"%{car1}%", f"%{car1}%", f"%{car2}%", f"%{car2}%"))
    
    comparisons = cur.fetchall()
    if comparisons:
        response += "**User Comparisons:**\n"
        for i, (text,) in enumerate(comparisons, 1):
            response += f"{i}. {text[:200]}...\n\n"
    
    return response


@log_function_call(ai_logger)
def analyze_fuel_average(car_brand, cur):
    """Analyze fuel average for specific car"""
    cur.execute("""
        SELECT cooked_text, author FROM posts 
        WHERE (LOWER(topic_title) LIKE ? OR LOWER(cooked_text) LIKE ?)
        AND (LOWER(cooked_text) LIKE '%fuel%' OR LOWER(cooked_text) LIKE '%mileage%' OR LOWER(cooked_text) LIKE '%average%')
        LIMIT 15
    """, (f"%{car_brand}%", f"%{car_brand}%"))
    
    results = cur.fetchall()
    
    if not results:
        return f"I don't have fuel average data for {car_brand.title()} yet."
    
    response = f"⛽ **Fuel Average for {car_brand.upper()}**\n\n"
    response += f"Based on {len(results)} user reports:\n\n"
    
    for i, (text, author) in enumerate(results[:5], 1):
        response += f"{i}. {text[:200]}...\n   (by {author})\n\n"
    
    return response


@log_function_call(ai_logger)
def analyze_general_fuel(query, cur):
    """Analyze general fuel discussions"""
    cur.execute("""
        SELECT topic_title, cooked_text, author FROM posts 
        WHERE LOWER(cooked_text) LIKE '%fuel%' OR LOWER(cooked_text) LIKE '%mileage%'
        LIMIT 10
    """)
    results = cur.fetchall()
    
    if not results:
        return "No fuel average discussions found in the database."
    
    response = "⛽ **Fuel Average Discussions:**\n\n"
    for i, (title, text, author) in enumerate(results[:5], 1):
        response += f"{i}. **{title}**\n   {text[:150]}...\n   (by {author})\n\n"
    
    return response


@log_function_call(ai_logger)
def analyze_car_pricing(car_brand, cur):
    """Analyze pricing discussions for a car"""
    cur.execute("""
        SELECT cooked_text, author FROM posts 
        WHERE (LOWER(topic_title) LIKE ? OR LOWER(cooked_text) LIKE ?)
        AND (LOWER(cooked_text) LIKE '%price%' OR LOWER(cooked_text) LIKE '%cost%' OR LOWER(cooked_text) LIKE '%expensive%')
        LIMIT 10
    """, (f"%{car_brand}%", f"%{car_brand}%"))
    
    results = cur.fetchall()
    
    if not results:
        return f"No pricing discussions found for {car_brand.title()}."
    
    response = f"💰 **Pricing Discussions for {car_brand.upper()}**\n\n"
    for i, (text, author) in enumerate(results[:5], 1):
        response += f"{i}. {text[:200]}...\n   (by {author})\n\n"
    
    return response


@log_function_call(ai_logger)
def analyze_car_features(car_brand, cur):
    """Analyze features and specifications"""
    cur.execute("""
        SELECT cooked_text, author FROM posts 
        WHERE (LOWER(topic_title) LIKE ? OR LOWER(cooked_text) LIKE ?)
        AND (LOWER(cooked_text) LIKE '%feature%' OR LOWER(cooked_text) LIKE '%spec%' OR LOWER(cooked_text) LIKE '%technology%')
        LIMIT 10
    """, (f"%{car_brand}%", f"%{car_brand}%"))
    
    results = cur.fetchall()
    
    if not results:
        return f"No feature discussions found for {car_brand.title()}."
    
    response = f"✨ **Features & Specifications for {car_brand.upper()}**\n\n"
    for i, (text, author) in enumerate(results[:5], 1):
        response += f"{i}. {text[:200]}...\n   (by {author})\n\n"
    
    return response


@log_function_call(ai_logger)
def handle_statistics_query(query, cur):
    """Handle statistical queries"""
    if "post" in query:
        cur.execute("SELECT COUNT(*) FROM posts WHERE user_id = ?", (current_user.id,))
        count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM search_results WHERE user_id = ?", (current_user.id,))
        search_count = cur.fetchone()[0]
        return f"📊 **Database Statistics:**\n\n• Category posts: {count}\n• Search results: {search_count}\n• Total: {count + search_count}"
    
    if "topic" in query:
        cur.execute("SELECT COUNT(DISTINCT topic_title) FROM posts WHERE user_id = ?", (current_user.id,))
        count = cur.fetchone()[0]
        return f"📊 There are **{count}** unique topics in the database."
    
    if "author" in query or "user" in query:
        cur.execute("SELECT COUNT(DISTINCT author) FROM posts WHERE user_id = ?", (current_user.id,))
        count = cur.fetchone()[0]
        return f"📊 There are **{count}** unique authors/users in the database."
    
    return "Please specify what you want to count (posts, topics, or users)."


@log_function_call(ai_logger)
def handle_top_query(query, cur):
    """Handle top/best queries"""
    if "author" in query:
        cur.execute("SELECT author, COUNT(*) as count FROM posts GROUP BY author ORDER BY count DESC LIMIT 5")
        results = cur.fetchall()
        response = "🏆 **Top 5 Most Active Authors:**\n\n"
        for i, (author, count) in enumerate(results, 1):
            response += f"{i}. {author}: {count} posts\n"
        return response
    
    if "topic" in query:
        cur.execute("SELECT topic_title, COUNT(*) as count FROM posts GROUP BY topic_title ORDER BY count DESC LIMIT 5")
        results = cur.fetchall()
        response = "🔥 **Top 5 Most Discussed Topics:**\n\n"
        for i, (title, count) in enumerate(results, 1):
            response += f"{i}. {title[:60]}... ({count} posts)\n"
        return response
    
    return "What would you like to see the top of? (authors, topics, etc.)"


@log_function_call(ai_logger)
def search_car_discussions(car_brand, cur):
    """Search for general car discussions"""
    cur.execute("""
        SELECT topic_title, cooked_text, author FROM posts 
        WHERE LOWER(topic_title) LIKE ? OR LOWER(cooked_text) LIKE ?
        LIMIT 10
    """, (f"%{car_brand}%", f"%{car_brand}%"))
    
    results = cur.fetchall()
    
    if not results:
        return f"No discussions found about {car_brand.title()}. Try searching for it first!"
    
    response = f"💬 **Discussions about {car_brand.upper()}:**\n\n"
    response += f"Found {len(results)} relevant posts:\n\n"
    
    for i, (title, text, author) in enumerate(results[:5], 1):
        response += f"{i}. **{title}**\n   {text[:150]}...\n   (by {author})\n\n"
    
    return response


@log_function_call(ai_logger)
def intelligent_search(query, cur):
    """Intelligent keyword-based search"""
    # Extract meaningful words
    stop_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'what', 'how', 'why', 'when', 'where', 'about', 'tell', 'me', 'please'}
    words = [w.lower() for w in query.split() if w.lower() not in stop_words and len(w) > 2]
    
    if not words:
        return """🤖 **AI Chatbot Help**

I can help you with:
• Car reviews and opinions (e.g., "What do people think about Haval H6?")
• Common problems (e.g., "Haval H6 problems")
• Comparisons (e.g., "Compare Corolla vs Civic")
• Fuel average (e.g., "Haval fuel average")
• Pricing discussions (e.g., "Is MG HS expensive?")
• Features (e.g., "Kia Sportage features")
• Statistics (e.g., "How many posts about Toyota?")
• User analysis (e.g., "Show posts by john", "What did sarah say?")

What would you like to know?"""
    
    search_term = words[0]
    
    # Special test case for charts
    if search_term.lower() in ['chart', 'test', 'demo', 'sample']:
        return generate_sample_chart_response()
    
    cur.execute("""
        SELECT topic_title, cooked_text, author FROM posts 
        WHERE LOWER(topic_title) LIKE ? OR LOWER(cooked_text) LIKE ?
        LIMIT 10
    """, (f"%{search_term}%", f"%{search_term}%"))
    
    results = cur.fetchall()
    
    if not results:
        return f"I couldn't find any discussions about '{search_term}'. Try different keywords or search for it first!"
    
    response = f"🔍 **Search Results for '{search_term}':**\n\n"
    for i, (title, text, author) in enumerate(results[:5], 1):
        response += f"{i}. **{title}**\n   {text[:150]}...\n   (by {author})\n\n"
    
    return response


@log_function_call(ai_logger)
def generate_sample_chart_response():
    """Generate a sample response with charts for testing"""
    return """📊 **Sample Chart Demo**

Here's a sample chart showing car popularity:

```chart
type: bar
title: Car Brand Popularity
data: {"Haval": 45, "Toyota": 38, "Honda": 32, "Kia": 28, "Suzuki": 25}
```

And here's a pie chart showing issue types:

```chart
type: pie
title: Common Issues Distribution
data: {"Engine": 30, "Transmission": 25, "Electrical": 20, "AC": 15, "Other": 10}
```

**Analysis:**
• Haval leads in discussions with 45 mentions
• Engine issues are the most common concern (30%)
• Toyota and Honda show strong presence in forums

This demonstrates the chart rendering functionality!"""