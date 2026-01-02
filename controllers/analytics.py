from flask import render_template, request, jsonify, make_response
from flask_login import current_user, login_required
from models.analytics import Analytics
from models.whatsapp import WhatsAppMessage
from datetime import datetime
from utils.logger import analytics_logger, log_function_call, log_user_action, log_error


@log_function_call(analytics_logger)
def analysis():
    """Advanced analytics dashboard with sentiment analysis and complaint tracking"""
    # Get user's company
    user_company = current_user.company_id or 'haval'
    
    # Get date filter parameters
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    
    analytics_logger.info(f"Analytics dashboard accessed by user {current_user.username} for company {user_company}")
    analytics_logger.info(f"Date filter: {date_from} to {date_to}")
    
    # Get company configuration
    from config import get_company_config
    try:
        company_config = get_company_config(user_company)
        company_name = company_config.full_name
        analytics_logger.info(f"Company config loaded: {company_name}")
    except Exception as e:
        company_name = user_company.title()
        log_error(e, f"Failed to get company config for {user_company}")
    
    try:
        # Get analytics data
        analytics_logger.info("Fetching user analytics data...")
        user_analytics = Analytics.get_user_analytics(
            current_user.id,
            user_company, 
            date_from=date_from, 
            date_to=date_to
        )
        
        analytics_logger.info("Fetching sentiment analysis...")
        sentiment_analysis = Analytics.get_sentiment_analysis(
            user_company, 
            date_from=date_from, 
            date_to=date_to
        )
        
        analytics_logger.info("Fetching complaint analysis...")
        complaint_analysis = Analytics.get_complaint_analysis(
            user_company, 
            date_from=date_from, 
            date_to=date_to
        )
        
        analytics_logger.info("Fetching WhatsApp statistics...")
        whatsapp_stats = Analytics.get_whatsapp_analytics(
            user_company, 
            date_from=date_from, 
            date_to=date_to
        )
        
        # Pipeline analytics
        try:
            analytics_logger.info("Fetching pipeline analytics...")
            from ai.haval_pipeline import get_pipeline_status, get_daily_weekly_stats
            pipeline_status = get_pipeline_status()
            daily_stats, weekly_stats = get_daily_weekly_stats()
            analytics_logger.info(f"Pipeline status: {pipeline_status.get('status', 'unknown')}")
        except Exception as e:
            pipeline_status = {"status": "error", "error": str(e)}
            daily_stats, weekly_stats = [], []
            log_error(e, "Failed to get pipeline analytics")

        log_user_action("Analytics Dashboard", current_user.id, 
                       f"Company: {user_company}, Date range: {date_from} to {date_to}")
        
        analytics_logger.info(f"Analytics data compiled successfully for user {current_user.username}")
        
        # Check if this is an AJAX request for JSON data
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            analytics_logger.info("Returning JSON response for AJAX request")
            return jsonify({
                'success': True,
                'total_posts': user_analytics.get("total_posts", 0),
                'search_posts': user_analytics.get("search_posts", 0),
                'unique_topics': user_analytics.get("unique_topics", 0),
                'unique_authors': user_analytics.get("unique_authors", 0),
                'chatbot_usage': user_analytics.get("chatbot_usage", {}),
                'popular_queries': user_analytics.get("popular_queries", []),
                'sentiment_analysis': sentiment_analysis,
                'pakwheels_complaints': complaint_analysis.get("pakwheels", []),
                'whatsapp_complaints': complaint_analysis.get("whatsapp", []),
                'whatsapp_stats': whatsapp_stats,
                'date_from': date_from,
                'date_to': date_to,
                'filtered': bool(date_from or date_to)
            })
        
        # Return HTML template for regular requests
        return render_template(
            "analysis_pro.html",
            total_posts=user_analytics.get("total_posts", 0),
            search_posts=user_analytics.get("search_posts", 0),
            unique_topics=user_analytics.get("unique_topics", 0),
            unique_authors=user_analytics.get("unique_authors", 0),
            chatbot_usage=user_analytics.get("chatbot_usage", {}),
            popular_queries=user_analytics.get("popular_queries", []),
            sentiment_analysis=sentiment_analysis,
            pakwheels_complaints=complaint_analysis.get("pakwheels", []),
            whatsapp_complaints=complaint_analysis.get("whatsapp", []),
            pipeline_status=pipeline_status,
            daily_stats=daily_stats,
            weekly_stats=weekly_stats,
            whatsapp_stats=whatsapp_stats,
            user_company=user_company,
            company_name=company_name,
            selected_company=user_company,
            date_from=date_from,
            date_to=date_to,
        )
        
    except Exception as e:
        log_error(e, f"Error in analytics dashboard for user {current_user.username}")
        analytics_logger.error(f"Analytics dashboard error: {str(e)}")
        
        # Return JSON error for AJAX requests
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'success': False,
                'error': str(e),
                'message': 'Analytics data unavailable'
            }), 500
        
        # Return error template for regular requests
        return render_template("error.html", error="Analytics data unavailable")


@log_function_call(analytics_logger)
def generate_report():
    """Generate comprehensive analytics report with PDF support"""
    user_company = current_user.company_id or 'haval'
    
    analytics_logger.info(f"Generating comprehensive report for user {current_user.username}, company {user_company}")
    
    try:
        # Get request data
        if request.method == 'POST':
            data = request.get_json() or {}
            date_from = data.get('date_from')
            date_to = data.get('date_to')
            include_charts = data.get('include_charts', False)
            report_format = data.get('format', 'json')
        else:
            date_from = request.args.get('date_from')
            date_to = request.args.get('date_to')
            include_charts = request.args.get('include_charts', 'false').lower() == 'true'
            report_format = request.args.get('format', 'json')
        
        analytics_logger.info(f"Report parameters: date_from={date_from}, date_to={date_to}, format={report_format}")
        
        # Get analytics data with date filtering
        user_analytics = Analytics.get_user_analytics(
            current_user.id,
            user_company, 
            date_from=date_from, 
            date_to=date_to
        )
        
        sentiment_analysis = Analytics.get_sentiment_analysis(
            user_company, 
            date_from=date_from, 
            date_to=date_to
        )
        
        complaint_analysis = Analytics.get_complaint_analysis(
            user_company, 
            date_from=date_from, 
            date_to=date_to
        )
        
        whatsapp_stats = Analytics.get_whatsapp_analytics(
            user_company, 
            date_from=date_from, 
            date_to=date_to
        ) if user_company == 'haval' else {}
        
        # Get company configuration
        from config import get_company_config
        try:
            company_config = get_company_config(user_company)
            company_name = company_config.full_name
        except Exception as e:
            company_name = user_company.title()
        
        # Build comprehensive report data
        report_data = {
            "success": True,
            "generated_at": datetime.now().isoformat(),
            "company": {
                "name": company_name,
                "id": user_company,
                "type": "automotive" if user_company == 'haval' else "general"
            },
            "date_range": {
                "from": date_from,
                "to": date_to,
                "filtered": bool(date_from or date_to)
            },
            "summary": {
                "total_posts": user_analytics.get("total_posts", 0),
                "total_whatsapp_messages": whatsapp_stats.get("total_messages", 0) if user_company == 'haval' else 0,
                "total_chatbot_queries": sum(user_analytics.get("chatbot_usage", {}).values()),
                "pakwheels_complaints": len(complaint_analysis.get("pakwheels", [])),
                "whatsapp_complaints": len(complaint_analysis.get("whatsapp", [])) if user_company == 'haval' else 0,
                "total_complaints": len(complaint_analysis.get("pakwheels", [])) + (len(complaint_analysis.get("whatsapp", [])) if user_company == 'haval' else 0)
            },
            "sentiment_analysis": sentiment_analysis or {},
            "chatbot_usage": user_analytics.get("chatbot_usage", {}),
            "popular_queries": user_analytics.get("popular_queries", [])[:10],  # Top 10 queries
            "whatsapp_stats": whatsapp_stats if user_company == 'haval' else {},
            "complaints": {
                "pakwheels": complaint_analysis.get("pakwheels", [])[:20],  # Latest 20 complaints
                "whatsapp": complaint_analysis.get("whatsapp", [])[:20] if user_company == 'haval' else []
            },
            "recommendations": generate_recommendations(
                user_analytics, sentiment_analysis, complaint_analysis, whatsapp_stats, user_company
            ),
            "report_type": "comprehensive" if user_company == 'haval' else "posts_only"
        }
        
        # If PDF format requested, try to generate PDF
        if report_format == 'pdf':
            try:
                pdf_content = generate_pdf_report(report_data)
                if pdf_content:
                    analytics_logger.info("PDF report generated successfully")
                    
                    response = make_response(pdf_content)
                    response.headers['Content-Type'] = 'application/pdf'
                    response.headers['Content-Disposition'] = f'attachment; filename="{company_name}_Analytics_Report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf"'
                    
                    log_user_action("PDF Report Generation", current_user.id, 
                                   f"Company: {user_company}, Date range: {date_from} to {date_to}")
                    
                    return response
                else:
                    analytics_logger.warning("PDF generation failed, falling back to JSON")
            except Exception as e:
                analytics_logger.error(f"PDF generation error: {str(e)}")
                log_error(e, "PDF report generation failed")
        
        # Return JSON response (default or fallback)
        analytics_logger.info(f"Report generated successfully: {len(report_data)} data points")
        
        log_user_action("Report Generation", current_user.id, 
                       f"Company: {user_company}, Date range: {date_from} to {date_to}")
        
        return jsonify(report_data)
        
    except Exception as e:
        log_error(e, f"Error generating report for user {current_user.username}")
        analytics_logger.error(f"Report generation failed: {str(e)}")
        
        return jsonify({
            "success": False,
            "error": str(e),
            "generated_at": datetime.now().isoformat(),
            "report_type": "error_report"
        }), 500


def generate_recommendations(user_analytics, sentiment_analysis, complaint_analysis, whatsapp_stats, company):
    """Generate intelligent recommendations based on analytics data"""
    recommendations = []
    
    total_posts = user_analytics.get("total_posts", 0)
    total_complaints = len(complaint_analysis.get("pakwheels", [])) + len(complaint_analysis.get("whatsapp", []))
    
    # Sentiment-based recommendations
    if sentiment_analysis:
        positive = sentiment_analysis.get("positive", 0)
        negative = sentiment_analysis.get("negative", 0)
        
        if negative > positive:
            recommendations.append("High negative sentiment detected. Implement immediate customer satisfaction improvement initiatives.")
        elif positive > negative * 2:
            recommendations.append("Excellent positive sentiment. Consider leveraging satisfied customers for testimonials and referrals.")
    
    # Complaint rate recommendations
    if total_posts > 0:
        complaint_rate = (total_complaints / total_posts) * 100
        if complaint_rate > 15:
            recommendations.append(f"High complaint rate ({complaint_rate:.1f}%). Conduct root cause analysis and implement quality improvements.")
        elif complaint_rate < 5:
            recommendations.append("Low complaint rate indicates good product quality. Maintain current standards.")
    
    # Company-specific recommendations
    if company == 'haval':
        whatsapp_messages = whatsapp_stats.get("total_messages", 0)
        if whatsapp_messages > 0:
            recommendations.append("WhatsApp integration is active. Consider expanding automated response capabilities.")
        else:
            recommendations.append("Consider promoting WhatsApp support channel to improve customer accessibility.")
    
    # Chatbot recommendations
    chatbot_total = sum(user_analytics.get("chatbot_usage", {}).values())
    if chatbot_total > 100:
        recommendations.append("High chatbot engagement. Analyze conversation patterns to improve AI responses.")
    elif chatbot_total < 50:
        recommendations.append("Low chatbot usage. Improve discoverability and expand knowledge base.")
    
    return recommendations


def generate_pdf_report(report_data):
    """Generate PDF report with charts"""
    try:
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib import colors
        from reportlab.graphics.shapes import Drawing
        from reportlab.graphics.charts.piecharts import Pie
        from reportlab.graphics.charts.barcharts import VerticalBarChart
        from reportlab.lib.colors import HexColor
        import matplotlib.pyplot as plt
        import matplotlib
        matplotlib.use('Agg')  # Use non-interactive backend
        import io
        import base64
        from datetime import datetime
        
        analytics_logger.info("Starting PDF report generation...")
        
        # Create PDF buffer
        buffer = io.BytesIO()
        
        # Create PDF document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        
        # Get styles
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            textColor=colors.HexColor('#2563eb'),
            alignment=1  # Center alignment
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            spaceAfter=12,
            textColor=colors.HexColor('#1e40af'),
            borderWidth=1,
            borderColor=colors.HexColor('#e5e7eb'),
            borderPadding=5,
            backColor=colors.HexColor('#f8fafc')
        )
        
        # Story (content) list
        story = []
        
        # Title
        company_name = report_data['company']['name']
        story.append(Paragraph(f"INSIGHTS AI ANALYTICS REPORT", title_style))
        story.append(Paragraph(f"{company_name}", styles['Heading2']))
        story.append(Spacer(1, 20))
        
        # Report metadata
        generated_at = datetime.fromisoformat(report_data['generated_at'].replace('Z', '+00:00'))
        date_range = report_data['date_range']
        
        metadata_data = [
            ['Generated:', generated_at.strftime('%Y-%m-%d %H:%M:%S')],
            ['Company:', company_name],
            ['Report Type:', report_data['report_type'].replace('_', ' ').title()],
            ['Date Range:', f"{date_range['from'] or 'All Time'} to {date_range['to'] or 'Present'}"],
            ['Filtered:', 'Yes' if date_range['filtered'] else 'No']
        ]
        
        metadata_table = Table(metadata_data, colWidths=[2*inch, 4*inch])
        metadata_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f1f5f9')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e5e7eb'))
        ]))
        
        story.append(metadata_table)
        story.append(Spacer(1, 30))
        
        # Executive Summary
        story.append(Paragraph("EXECUTIVE SUMMARY", heading_style))
        
        summary = report_data['summary']
        summary_data = [
            ['Metric', 'Value'],
            ['Total Forum Posts', f"{summary['total_posts']:,}"],
            ['Total Complaints', f"{summary['total_complaints']:,}"],
            ['Chatbot Interactions', f"{summary['total_chatbot_queries']:,}"]
        ]
        
        # Add WhatsApp data if available
        if report_data['company']['id'] == 'haval' and summary['total_whatsapp_messages'] > 0:
            summary_data.append(['WhatsApp Messages', f"{summary['total_whatsapp_messages']:,}"])
        
        summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2563eb')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8fafc')),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e5e7eb'))
        ]))
        
        story.append(summary_table)
        story.append(Spacer(1, 20))
        
        # Generate and add charts
        charts_created = 0
        
        # Sentiment Analysis Chart
        sentiment_data = report_data.get('sentiment_analysis', {})
        if sentiment_data and any(sentiment_data.values()):
            try:
                chart_image = create_sentiment_chart(sentiment_data)
                if chart_image:
                    story.append(Paragraph("SENTIMENT ANALYSIS", heading_style))
                    story.append(chart_image)
                    story.append(Spacer(1, 20))
                    charts_created += 1
            except Exception as e:
                analytics_logger.error(f"Error creating sentiment chart: {e}")
        
        # Chatbot Usage Chart
        chatbot_data = report_data.get('chatbot_usage', {})
        if chatbot_data and any(chatbot_data.values()):
            try:
                chart_image = create_chatbot_chart(chatbot_data)
                if chart_image:
                    story.append(Paragraph("CHATBOT USAGE ANALYSIS", heading_style))
                    story.append(chart_image)
                    story.append(Spacer(1, 20))
                    charts_created += 1
            except Exception as e:
                analytics_logger.error(f"Error creating chatbot chart: {e}")
        
        # WhatsApp Analysis (if Haval)
        if report_data['company']['id'] == 'haval':
            whatsapp_stats = report_data.get('whatsapp_stats', {})
            if whatsapp_stats.get('message_types') and any(whatsapp_stats['message_types'].values()):
                try:
                    chart_image = create_whatsapp_chart(whatsapp_stats['message_types'])
                    if chart_image:
                        story.append(Paragraph("WHATSAPP MESSAGE ANALYSIS", heading_style))
                        story.append(chart_image)
                        story.append(Spacer(1, 20))
                        charts_created += 1
                except Exception as e:
                    analytics_logger.error(f"Error creating WhatsApp chart: {e}")
        
        # Popular Queries
        popular_queries = report_data.get('popular_queries', [])
        if popular_queries:
            story.append(Paragraph("TOP CUSTOMER QUERIES", heading_style))
            
            queries_data = [['Query', 'Frequency']]
            for query in popular_queries[:10]:
                query_text = query['query'][:50] + '...' if len(query['query']) > 50 else query['query']
                queries_data.append([query_text, str(query['count'])])
            
            queries_table = Table(queries_data, colWidths=[4*inch, 1*inch])
            queries_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#8b5cf6')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (1, 0), (1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#faf5ff')),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e5e7eb'))
            ]))
            
            story.append(queries_table)
            story.append(Spacer(1, 20))
        
        # Recommendations
        recommendations = report_data.get('recommendations', [])
        if recommendations:
            story.append(Paragraph("RECOMMENDATIONS", heading_style))
            
            for i, rec in enumerate(recommendations, 1):
                story.append(Paragraph(f"{i}. {rec}", styles['Normal']))
                story.append(Spacer(1, 8))
        
        # Complaints Analysis
        complaints = report_data.get('complaints', {})
        pakwheels_complaints = complaints.get('pakwheels', [])
        whatsapp_complaints = complaints.get('whatsapp', [])
        
        if pakwheels_complaints or whatsapp_complaints:
            story.append(PageBreak())
            story.append(Paragraph("RECENT COMPLAINTS ANALYSIS", heading_style))
            
            if pakwheels_complaints:
                story.append(Paragraph("PakWheels Forum Complaints", styles['Heading3']))
                
                complaints_data = [['Date', 'Author', 'Complaint Summary']]
                for complaint in pakwheels_complaints[:10]:
                    complaint_text = complaint.get('text', '')[:80] + '...' if len(complaint.get('text', '')) > 80 else complaint.get('text', '')
                    complaints_data.append([
                        complaint.get('date', 'N/A'),
                        complaint.get('author', 'Anonymous')[:20],
                        complaint_text
                    ])
                
                complaints_table = Table(complaints_data, colWidths=[1.5*inch, 1.5*inch, 3*inch])
                complaints_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#ef4444')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 8),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#fef2f2')),
                    ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e5e7eb')),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP')
                ]))
                
                story.append(complaints_table)
                story.append(Spacer(1, 15))
            
            if whatsapp_complaints and report_data['company']['id'] == 'haval':
                story.append(Paragraph("WhatsApp Complaints", styles['Heading3']))
                
                wa_complaints_data = [['Date', 'Customer', 'Message Summary']]
                for complaint in whatsapp_complaints[:10]:
                    message_text = complaint.get('message', '')[:80] + '...' if len(complaint.get('message', '')) > 80 else complaint.get('message', '')
                    wa_complaints_data.append([
                        complaint.get('date', 'N/A'),
                        complaint.get('customer', 'Anonymous')[:20],
                        message_text
                    ])
                
                wa_complaints_table = Table(wa_complaints_data, colWidths=[1.5*inch, 1.5*inch, 3*inch])
                wa_complaints_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#25d366')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 8),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f0fff4')),
                    ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e5e7eb')),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP')
                ]))
                
                story.append(wa_complaints_table)
        
        # Footer
        story.append(Spacer(1, 30))
        story.append(Paragraph("Generated by Insights AI Analytics Platform", styles['Normal']))
        story.append(Paragraph(f"© {datetime.now().year} - Advanced Analytics & Business Intelligence", styles['Normal']))
        
        # Build PDF
        doc.build(story)
        
        # Get PDF content
        pdf_content = buffer.getvalue()
        buffer.close()
        
        analytics_logger.info(f"PDF report generated successfully with {charts_created} charts")
        return pdf_content
        
    except Exception as e:
        analytics_logger.error(f"PDF generation error: {str(e)}")
        import traceback
        analytics_logger.error(f"PDF generation traceback: {traceback.format_exc()}")
        return None


def create_sentiment_chart(sentiment_data):
    """Create sentiment analysis pie chart"""
    try:
        import matplotlib.pyplot as plt
        import io
        from reportlab.platypus import Image
        
        # Create figure
        fig, ax = plt.subplots(figsize=(6, 4))
        
        labels = list(sentiment_data.keys())
        values = list(sentiment_data.values())
        colors_list = ['#10b981', '#f59e0b', '#ef4444', '#3b82f6']
        
        # Create pie chart
        wedges, texts, autotexts = ax.pie(values, labels=labels, autopct='%1.1f%%', 
                                         colors=colors_list[:len(labels)], startangle=90)
        
        ax.set_title('Sentiment Analysis Distribution', fontsize=14, fontweight='bold')
        
        # Save to buffer
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
        buffer.seek(0)
        
        # Create ReportLab Image
        img = Image(buffer, width=4*inch, height=3*inch)
        
        plt.close()
        return img
        
    except Exception as e:
        analytics_logger.error(f"Error creating sentiment chart: {e}")
        return None


def create_chatbot_chart(chatbot_data):
    """Create chatbot usage bar chart"""
    try:
        import matplotlib.pyplot as plt
        import io
        from reportlab.platypus import Image
        
        # Create figure
        fig, ax = plt.subplots(figsize=(6, 4))
        
        labels = list(chatbot_data.keys())
        values = list(chatbot_data.values())
        
        # Create bar chart
        bars = ax.bar(labels, values, color='#6366f1')
        
        ax.set_title('Chatbot Usage by Mode', fontsize=14, fontweight='bold')
        ax.set_xlabel('Mode')
        ax.set_ylabel('Number of Queries')
        
        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{int(height)}', ha='center', va='bottom')
        
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        # Save to buffer
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
        buffer.seek(0)
        
        # Create ReportLab Image
        img = Image(buffer, width=4*inch, height=3*inch)
        
        plt.close()
        return img
        
    except Exception as e:
        analytics_logger.error(f"Error creating chatbot chart: {e}")
        return None


def create_whatsapp_chart(whatsapp_data):
    """Create WhatsApp message types pie chart"""
    try:
        import matplotlib.pyplot as plt
        import io
        from reportlab.platypus import Image
        
        # Create figure
        fig, ax = plt.subplots(figsize=(6, 4))
        
        labels = list(whatsapp_data.keys())
        values = list(whatsapp_data.values())
        colors_list = ['#25d366', '#ef4444', '#3b82f6']
        
        # Create pie chart
        wedges, texts, autotexts = ax.pie(values, labels=labels, autopct='%1.1f%%', 
                                         colors=colors_list[:len(labels)], startangle=90)
        
        ax.set_title('WhatsApp Message Types Distribution', fontsize=14, fontweight='bold')
        
        # Save to buffer
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
        buffer.seek(0)
        
        # Create ReportLab Image
        img = Image(buffer, width=4*inch, height=3*inch)
        
        plt.close()
        return img
        
    except Exception as e:
        analytics_logger.error(f"Error creating WhatsApp chart: {e}")
        return None


@log_function_call(analytics_logger)
def db_summary():
    """Get database summary for current user"""
    from models.database import get_db_connection
    
    analytics_logger.info(f"Fetching database summary for user {current_user.username}")
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # User's posts
        cur.execute("SELECT COUNT(*) FROM posts WHERE user_id = ?", (current_user.id,))
        total = cur.fetchone()[0]
        
        # Posts by category
        cur.execute("SELECT category, COUNT(*) FROM posts WHERE user_id = ? GROUP BY category", (current_user.id,))
        by_cat = [{"category": row[0], "count": row[1]} for row in cur.fetchall()]
        
        # Search results
        cur.execute("SELECT COUNT(*) FROM search_results WHERE user_id = ?", (current_user.id,))
        search_total = cur.fetchone()[0]
        
        conn.close()
        
        analytics_logger.info(f"Database summary: {total} posts, {len(by_cat)} categories, {search_total} search results")
        
        log_user_action("Database Summary", current_user.id, 
                       f"Posts: {total}, Categories: {len(by_cat)}, Search: {search_total}")
        
        return jsonify({
            "total_posts": total, 
            "by_category": by_cat, 
            "search_results": search_total
        })
        
    except Exception as e:
        log_error(e, f"Error getting database summary for user {current_user.username}")
        analytics_logger.error(f"Database summary error: {str(e)}")
        
        return jsonify({
            "error": str(e),
            "total_posts": 0,
            "by_category": [],
            "search_results": 0
        })