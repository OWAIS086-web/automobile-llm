from datetime import datetime, timedelta
from models.database import get_db_connection
from typing import Dict, List, Optional


class Analytics:
    """Analytics model for handling various analytics operations"""
    
    @staticmethod
    def get_user_analytics(user_id: int, company_id: str, date_from: str = None, 
                          date_to: str = None) -> Dict:
        """Get comprehensive analytics for a user"""
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Build date filter
        date_filter = ""
        date_params = []
        if date_from:
            date_filter += " AND created_at >= ?"
            date_params.append(date_from)
        if date_to:
            date_filter += " AND created_at <= ?"
            date_params.append(date_to + " 23:59:59")
        
        analytics = {}
        
        # Basic post statistics
        cur.execute(f"SELECT COUNT(*) FROM posts WHERE user_id = ? AND company_id = ?{date_filter}", 
                   [user_id, company_id] + date_params)
        analytics['total_posts'] = cur.fetchone()[0]
        
        cur.execute(f"SELECT COUNT(*) FROM search_results WHERE user_id = ? AND company_id = ?{date_filter}", 
                   [user_id, company_id] + date_params)
        analytics['search_posts'] = cur.fetchone()[0]
        
        cur.execute(f"SELECT COUNT(DISTINCT topic_title) FROM posts WHERE user_id = ? AND company_id = ?{date_filter}", 
                   [user_id, company_id] + date_params)
        analytics['unique_topics'] = cur.fetchone()[0]
        
        cur.execute(f"SELECT COUNT(DISTINCT author) FROM posts WHERE user_id = ? AND company_id = ?{date_filter}", 
                   [user_id, company_id] + date_params)
        analytics['unique_authors'] = cur.fetchone()[0]
        
        # Chat analytics
        chat_date_filter = ""
        chat_date_params = []
        if date_from:
            chat_date_filter += " AND timestamp >= ?"
            chat_date_params.append(date_from)
        if date_to:
            chat_date_filter += " AND timestamp <= ?"
            chat_date_params.append(date_to + " 23:59:59")
        
        cur.execute(f"""
            SELECT mode, COUNT(*) as count 
            FROM chat_history 
            WHERE user_id = ?{chat_date_filter}
            GROUP BY mode 
            ORDER BY count DESC
        """, [user_id] + chat_date_params)
        analytics['chatbot_usage'] = {row[0]: row[1] for row in cur.fetchall()}
        
        # Popular queries
        cur.execute(f"""
            SELECT query, COUNT(*) as count 
            FROM chat_history 
            WHERE user_id = ? AND LENGTH(query) > 10{chat_date_filter}
            GROUP BY LOWER(query) 
            ORDER BY count DESC 
            LIMIT 10
        """, [user_id] + chat_date_params)
        analytics['popular_queries'] = [{"query": row[0], "count": row[1]} for row in cur.fetchall()]
        
        conn.close()
        return analytics
    
    @staticmethod
    def get_sentiment_analysis(company_id: str, date_from: str = None, 
                              date_to: str = None) -> Dict:
        """Analyze sentiment in posts and WhatsApp messages"""
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Build date filter
        date_filter = ""
        date_params = []
        if date_from:
            date_filter += " AND created_at >= ?"
            date_params.append(date_from)
        if date_to:
            date_filter += " AND created_at <= ?"
            date_params.append(date_to + " 23:59:59")
        
        positive_keywords = ['good', 'great', 'excellent', 'amazing', 'love', 'best', 'perfect', 'recommend', 'happy', 'satisfied']
        negative_keywords = ['bad', 'poor', 'worst', 'hate', 'terrible', 'awful', 'disappointed', 'problem', 'issue', 'complaint']
        
        # Analyze posts sentiment
        cur.execute(f"SELECT cooked_text FROM posts WHERE company_id = ?{date_filter}", 
                   [company_id] + date_params)
        posts_text = [row[0].lower() for row in cur.fetchall()]
        
        positive_count = 0
        negative_count = 0
        neutral_count = 0
        
        for text in posts_text:
            pos_score = sum(1 for word in positive_keywords if word in text)
            neg_score = sum(1 for word in negative_keywords if word in text)
            
            if pos_score > neg_score:
                positive_count += 1
            elif neg_score > pos_score:
                negative_count += 1
            else:
                neutral_count += 1
        
        return {
            'positive': positive_count,
            'negative': negative_count,
            'neutral': neutral_count,
            'total_analyzed': len(posts_text)
        }
    
    @staticmethod
    def get_complaint_analysis(company_id: str, date_from: str = None, 
                              date_to: str = None) -> Dict:
        """Analyze complaints from posts and WhatsApp"""
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Build date filter
        date_filter = ""
        date_params = []
        if date_from:
            date_filter += " AND created_at >= ?"
            date_params.append(date_from)
        if date_to:
            date_filter += " AND created_at <= ?"
            date_params.append(date_to + " 23:59:59")
        
        complaints = {}
        
        # PakWheels complaints
        cur.execute(f"""
            SELECT cooked_text, author, created_at FROM posts 
            WHERE company_id = ?{date_filter} AND (
                LOWER(cooked_text) LIKE '%problem%' OR 
                LOWER(cooked_text) LIKE '%issue%' OR 
                LOWER(cooked_text) LIKE '%complaint%' OR 
                LOWER(cooked_text) LIKE '%defect%' OR 
                LOWER(cooked_text) LIKE '%fault%'
            )
            ORDER BY created_at DESC
            LIMIT 20
        """, [company_id] + date_params)
        
        complaints['pakwheels'] = [
            {"text": row[0][:200], "author": row[1], "date": row[2]} 
            for row in cur.fetchall()
        ]
        
        # WhatsApp complaints
        whatsapp_date_filter = date_filter.replace('created_at', 'timestamp') if date_filter else ""
        try:
            cur.execute(f"""
                SELECT customer_name, message, timestamp 
                FROM whatsapp_messages 
                WHERE company_id = ? AND message_type = 'complaint'{whatsapp_date_filter}
                ORDER BY timestamp DESC
                LIMIT 20
            """, [company_id] + date_params)
            
            complaints['whatsapp'] = [
                {"customer": row[0], "message": row[1][:200], "date": row[2]} 
                for row in cur.fetchall()
            ]
        except:
            complaints['whatsapp'] = []
        
        conn.close()
        return complaints
    
    @staticmethod
    def get_whatsapp_analytics(company_id: str, date_from: str = None, 
                              date_to: str = None) -> Dict:
        """Get WhatsApp specific analytics"""
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Build date filter for WhatsApp
        date_filter = ""
        date_params = []
        if date_from:
            date_filter += " AND timestamp >= ?"
            date_params.append(date_from)
        if date_to:
            date_filter += " AND timestamp <= ?"
            date_params.append(date_to + " 23:59:59")
        
        analytics = {}
        
        try:
            # Message type distribution
            cur.execute(f"""
                SELECT message_type, COUNT(*) as count 
                FROM whatsapp_messages 
                WHERE company_id = ?{date_filter}
                GROUP BY message_type 
                ORDER BY count DESC
            """, [company_id] + date_params)
            analytics['message_types'] = {row[0]: row[1] for row in cur.fetchall()}
            
            # Total messages
            cur.execute(f"SELECT COUNT(*) FROM whatsapp_messages WHERE company_id = ?{date_filter}", 
                       [company_id] + date_params)
            analytics['total_messages'] = cur.fetchone()[0]
            
            # Common queries
            cur.execute(f"""
                SELECT message, COUNT(*) as count 
                FROM whatsapp_messages 
                WHERE company_id = ? AND message_type = 'query' AND sender = 'customer' AND LENGTH(message) > 10{date_filter}
                GROUP BY LOWER(message) 
                ORDER BY count DESC 
                LIMIT 10
            """, [company_id] + date_params)
            analytics['common_queries'] = [{"query": row[0], "count": row[1]} for row in cur.fetchall()]
            
            # Daily activity
            activity_filter = date_filter if date_filter else " AND timestamp >= datetime('now', '-7 days')"
            cur.execute(f"""
                SELECT DATE(timestamp) as date, COUNT(*) as count
                FROM whatsapp_messages 
                WHERE company_id = ?{activity_filter}
                GROUP BY DATE(timestamp)
                ORDER BY date DESC
            """, [company_id] + (date_params if date_filter else []))
            analytics['daily_activity'] = {row[0]: row[1] for row in cur.fetchall()}
            
        except Exception as e:
            # WhatsApp table might not exist or have issues
            analytics = {
                'message_types': {},
                'total_messages': 0,
                'daily_activity': {},
                'common_queries': []
            }
        
        conn.close()
        return analytics
    
    @staticmethod
    def generate_comprehensive_report(company_id: str = None) -> Dict:
        """Generate comprehensive analytics report"""
        conn = get_db_connection()
        cur = conn.cursor()
        
        report = {
            "generated_at": datetime.now().isoformat(),
            "report_type": "comprehensive_analytics",
            "company_id": company_id,
            "summary": {}
        }
        
        if company_id:
            # Company-specific report
            cur.execute("SELECT COUNT(*) FROM posts WHERE company_id = ?", (company_id,))
            report["summary"]["total_posts"] = cur.fetchone()[0]
            
            try:
                cur.execute("SELECT COUNT(*) FROM whatsapp_messages WHERE company_id = ?", (company_id,))
                report["summary"]["total_whatsapp_messages"] = cur.fetchone()[0]
            except:
                report["summary"]["total_whatsapp_messages"] = 0
            
            cur.execute("SELECT COUNT(*) FROM chat_history WHERE user_id IN (SELECT id FROM users WHERE company_id = ?)", (company_id,))
            report["summary"]["total_chatbot_queries"] = cur.fetchone()[0]
            
        else:
            # Global report
            cur.execute("SELECT COUNT(*) FROM posts")
            report["summary"]["total_posts"] = cur.fetchone()[0]
            
            try:
                cur.execute("SELECT COUNT(*) FROM whatsapp_messages")
                report["summary"]["total_whatsapp_messages"] = cur.fetchone()[0]
            except:
                report["summary"]["total_whatsapp_messages"] = 0
            
            cur.execute("SELECT COUNT(*) FROM chat_history")
            report["summary"]["total_chatbot_queries"] = cur.fetchone()[0]
        
        # Complaint analysis
        if company_id:
            cur.execute("""
                SELECT COUNT(*) FROM posts 
                WHERE company_id = ? AND (
                    LOWER(cooked_text) LIKE '%problem%' OR 
                    LOWER(cooked_text) LIKE '%issue%' OR 
                    LOWER(cooked_text) LIKE '%complaint%'
                )
            """, (company_id,))
            report["summary"]["pakwheels_complaints"] = cur.fetchone()[0]
            
            try:
                cur.execute("SELECT COUNT(*) FROM whatsapp_messages WHERE company_id = ? AND message_type = 'complaint'", (company_id,))
                report["summary"]["whatsapp_complaints"] = cur.fetchone()[0]
            except:
                report["summary"]["whatsapp_complaints"] = 0
        else:
            cur.execute("""
                SELECT COUNT(*) FROM posts 
                WHERE (
                    LOWER(cooked_text) LIKE '%problem%' OR 
                    LOWER(cooked_text) LIKE '%issue%' OR 
                    LOWER(cooked_text) LIKE '%complaint%'
                )
            """)
            report["summary"]["pakwheels_complaints"] = cur.fetchone()[0]
            
            try:
                cur.execute("SELECT COUNT(*) FROM whatsapp_messages WHERE message_type = 'complaint'")
                report["summary"]["whatsapp_complaints"] = cur.fetchone()[0]
            except:
                report["summary"]["whatsapp_complaints"] = 0
        
        # Most active periods
        cur.execute("""
            SELECT DATE(timestamp) as date, COUNT(*) as count
            FROM chat_history 
            GROUP BY DATE(timestamp)
            ORDER BY count DESC
            LIMIT 5
        """)
        report["most_active_days"] = [{"date": row[0], "queries": row[1]} for row in cur.fetchall()]
        
        # Additional insights
        if company_id:
            cur.execute("SELECT COUNT(DISTINCT author) FROM posts WHERE company_id = ?", (company_id,))
            report["summary"]["unique_authors"] = cur.fetchone()[0]
            
            try:
                cur.execute("SELECT COUNT(DISTINCT customer_name) FROM whatsapp_messages WHERE company_id = ?", (company_id,))
                report["summary"]["unique_whatsapp_customers"] = cur.fetchone()[0]
            except:
                report["summary"]["unique_whatsapp_customers"] = 0
        else:
            cur.execute("SELECT COUNT(DISTINCT author) FROM posts")
            report["summary"]["unique_authors"] = cur.fetchone()[0]
            
            try:
                cur.execute("SELECT COUNT(DISTINCT customer_name) FROM whatsapp_messages")
                report["summary"]["unique_whatsapp_customers"] = cur.fetchone()[0]
            except:
                report["summary"]["unique_whatsapp_customers"] = 0
        
        conn.close()
        return report
    
    @staticmethod
    def get_daily_stats(company_id: str = None, days: int = 30) -> List[Dict]:
        """Get daily statistics for the last N days"""
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Generate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        stats = []
        
        for i in range(days):
            current_date = start_date + timedelta(days=i)
            date_str = current_date.strftime('%Y-%m-%d')
            
            day_stats = {
                'date': date_str,
                'posts': 0,
                'whatsapp_messages': 0,
                'chat_queries': 0
            }
            
            # Posts count
            if company_id:
                cur.execute("SELECT COUNT(*) FROM posts WHERE company_id = ? AND DATE(created_at) = ?", 
                           (company_id, date_str))
            else:
                cur.execute("SELECT COUNT(*) FROM posts WHERE DATE(created_at) = ?", (date_str,))
            day_stats['posts'] = cur.fetchone()[0]
            
            # WhatsApp messages count
            try:
                if company_id:
                    cur.execute("SELECT COUNT(*) FROM whatsapp_messages WHERE company_id = ? AND DATE(timestamp) = ?", 
                               (company_id, date_str))
                else:
                    cur.execute("SELECT COUNT(*) FROM whatsapp_messages WHERE DATE(timestamp) = ?", (date_str,))
                day_stats['whatsapp_messages'] = cur.fetchone()[0]
            except:
                day_stats['whatsapp_messages'] = 0
            
            # Chat queries count
            if company_id:
                cur.execute("""
                    SELECT COUNT(*) FROM chat_history 
                    WHERE user_id IN (SELECT id FROM users WHERE company_id = ?) 
                    AND DATE(timestamp) = ?
                """, (company_id, date_str))
            else:
                cur.execute("SELECT COUNT(*) FROM chat_history WHERE DATE(timestamp) = ?", (date_str,))
            day_stats['chat_queries'] = cur.fetchone()[0]
            
            stats.append(day_stats)
        
        conn.close()
        return stats