from flask import render_template, request, redirect, url_for, send_file, jsonify, flash
from flask_login import login_required, current_user
from controllers.scraping import (
    fetch_categories, collect_all_topics_from_category, 
    fetch_posts_for_topic_via_json, export_topic_posts_to_files
)
from models.post import Post
from models.database import get_user_data_dir
import os
import time


def index():
    """Redirect to chatbot as the main page"""
    return redirect(url_for('chatbot_advanced'))


def download_file():
    """Download file endpoint"""
    path = request.args.get("path")
    if not path or not os.path.exists(path):
        return "File not found", 404
    return send_file(path, as_attachment=True)


def scrape_single_topic():
    """Scrape PakWheels discussion thread for selected company"""
    
    if request.method != "POST":
        return redirect(url_for('chatbot_advanced'))
    
    # Get user's company
    user_company = current_user.company_id or 'haval'
    
    # Get company configuration
    from config import get_company_config
    try:
        company_config = get_company_config(user_company)
        company_name = company_config.full_name
        thread_url = company_config.pakwheels_url  # Fix: use pakwheels_url instead of thread_url
    except Exception as e:
        flash(f"Error getting company configuration: {e}", "error")
        return redirect(url_for('chatbot_advanced'))
    
    # Validate thread URL
    if not thread_url or not thread_url.strip():
        flash(f"No PakWheels URL configured for {company_name}. Please check settings.", "error")
        return redirect(url_for('chatbot_advanced'))
    
    # Get form parameters
    max_posts = int(request.form.get("max_posts", 1000))
    fetch_mode = request.form.get("fetch_mode", "latest")  # "latest" or "oldest"
    
    # Validate max_posts
    if max_posts > 10000:
        max_posts = 10000
        flash("Maximum posts limited to 10,000 for performance reasons.", "warning")
    
    try:
        start_time = time.time()
        
        # Determine if we want descending order (latest first)
        descending = (fetch_mode == "latest")
        
        flash(f"Starting to scrape {company_name} discussion thread...", "info")
        flash(f"Target: {max_posts} posts ({'latest' if descending else 'oldest'} first)", "info")
        
        # Fetch posts from the thread
        posts = fetch_posts_for_topic_via_json(
            topic_url=thread_url,
            max_posts=max_posts,
            descending=descending
        )
        
        if not posts:
            flash(f"❌ No posts found in {company_name} thread.", "error")
            flash("🔧 Possible causes:", "info")
            flash("• Thread may have been deleted or moved", "info")
            flash("• Network connectivity issues", "info")
            flash("• PakWheels server may be down", "info")
            flash("• Invalid thread URL in configuration", "info")
            flash("💡 Please check the thread URL and try again later", "info")
            return redirect(url_for('chatbot_advanced'))
        
        # Save posts to database
        saved_count, skipped_count = Post.save_posts_to_db(
            category_name=f"{company_name} Discussion",
            topic_title=f"{company_name} Dedicated Discussion Thread",
            topic_url=thread_url,
            posts=posts,
            user_id=current_user.id,
            company_id=user_company
        )
        
        # Export to files
        json_path, csv_path = export_topic_posts_to_files(
            category_slug=user_company,
            topic_title=f"{company_name} Discussion",
            topic_url=thread_url,
            posts=posts
        )
        
        elapsed_time = time.time() - start_time
        
        # Add detailed logging for debugging
        from utils.logger import server_logger
        server_logger.info(f"Scraping results: {len(posts)} posts fetched, {saved_count} saved, {skipped_count} skipped")
        
        flash(f"✅ Scraping completed in {elapsed_time:.1f}s", "success")
        flash(f"📊 Saved {saved_count} new posts, skipped {skipped_count} duplicates", "info")
        flash(f"📁 Files saved: {os.path.basename(json_path)}, {os.path.basename(csv_path)}", "info")
        
        # Start pipeline processing for the scraped data (always start if we have posts, even if duplicates)
        # This ensures the pipeline runs and users can see progress
        if len(posts) > 0:
            try:
                server_logger.info(f"Attempting to start pipeline for {company_name} with {len(posts)} posts ({saved_count} new, {skipped_count} duplicates)")
                
                from ai.haval_pipeline import start_haval_pipeline
                
                # Start pipeline with the exported JSON file (use correct case for sources)
                start_haval_pipeline(
                    json_path=json_path,
                    topic_url=thread_url,
                    sources="Pakwheels",  # Use capital P for Pakwheels
                    company_id=user_company
                )
                
                flash(f"🚀 Started AI pipeline processing for {company_name} data", "info")
                flash(f"📊 Processing {len(posts)} posts - check progress in real-time", "info")
                server_logger.info(f"Pipeline started successfully for {company_name}")
                
            except Exception as e:
                from utils.logger import log_error
                log_error(e, f"Pipeline startup failed for {company_name}")
                flash(f"⚠️ Scraping completed but pipeline startup failed: {str(e)}", "warning")
                server_logger.error(f"Pipeline startup error: {str(e)}")
        else:
            server_logger.info(f"No posts to process - pipeline startup skipped (fetched: {len(posts)}, saved: {saved_count}, skipped: {skipped_count})")
        
    except Exception as e:
        from utils.logger import log_error
        log_error(e, f"Scraping failed for {company_name}")
        flash(f"❌ Error during scraping: {str(e)}", "error")
        flash("🔧 This could be due to:", "info")
        flash("• Network connectivity issues", "info")
        flash("• PakWheels server problems", "info")
        flash("• Invalid thread URL", "info")
        flash("• Rate limiting", "info")
        flash("💡 Please try again later", "info")
    
    return redirect(url_for('chatbot_advanced'))


def pipeline_status():
    """Return JSON describing the current pipeline status"""
    try:
        from ai.haval_pipeline import get_pipeline_status
        status = get_pipeline_status()
        return jsonify(status)
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e),
            "message": "Pipeline status unavailable"
        })