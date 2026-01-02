from flask import render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, current_user
from datetime import datetime
from models.user import User
from models.database import get_db_connection
from utils.logger import auth_logger, log_function_call, log_user_action, log_error


@log_function_call(auth_logger)
def login():
    """Handle user login"""
    if current_user.is_authenticated:
        auth_logger.info(f"Already authenticated user {current_user.username} attempted login")
        return redirect(url_for('chatbot_advanced'))
    
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        remember = bool(request.form.get("remember"))
        
        auth_logger.info(f"Login attempt for username: {username}")
        
        if not username or not password:
            auth_logger.warning(f"Login failed - missing credentials for username: {username}")
            flash("Please enter both username and password.", "error")
            return render_template("auth/login.html")
        
        user = User.get_by_username(username)
        if user and User.verify_password(username, password):
            # Update last login
            try:
                conn = get_db_connection()
                cur = conn.cursor()
                cur.execute("UPDATE users SET last_login = ? WHERE id = ?", 
                           (datetime.now().isoformat(), user.id))
                conn.commit()
                conn.close()
                
                login_user(user, remember=remember)
                auth_logger.info(f"Successful login for user: {username} (ID: {user.id})")
                log_user_action("Login Success", user.id, f"Username: {username}, Remember: {remember}")
                flash(f"Welcome back, {user.username}!", "success")
                
                next_page = request.args.get('next')
                return redirect(next_page) if next_page else redirect(url_for('chatbot_advanced'))
                
            except Exception as e:
                log_error(e, f"Failed to update last login for user: {username}")
                # Still allow login even if last_login update fails
                login_user(user, remember=remember)
                flash(f"Welcome back, {user.username}!", "success")
                return redirect(url_for('chatbot_advanced'))
        else:
            auth_logger.warning(f"Login failed - invalid credentials for username: {username}")
            log_user_action("Login Failed", None, f"Username: {username}")
            flash("Invalid username or password.", "error")
    
    return render_template("auth/login.html")


@log_function_call(auth_logger)
def register():
    """Handle user registration"""
    if current_user.is_authenticated:
        auth_logger.info(f"Already authenticated user {current_user.username} attempted registration")
        return redirect(url_for('chatbot_advanced'))
    
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        company_id = request.form.get("company_id", "haval").strip()
        
        auth_logger.info(f"Registration attempt for username: {username}, email: {email}, company: {company_id}")
        
        # Validation
        if not all([username, email, password, confirm_password]):
            auth_logger.warning(f"Registration failed - missing fields for username: {username}")
            flash("All fields are required.", "error")
            return render_template("auth/register.html")
        
        if password != confirm_password:
            auth_logger.warning(f"Registration failed - password mismatch for username: {username}")
            flash("Passwords do not match.", "error")
            return render_template("auth/register.html")
        
        if len(password) < 6:
            auth_logger.warning(f"Registration failed - password too short for username: {username}")
            flash("Password must be at least 6 characters long.", "error")
            return render_template("auth/register.html")
        
        if len(username) < 3:
            auth_logger.warning(f"Registration failed - username too short: {username}")
            flash("Username must be at least 3 characters long.", "error")
            return render_template("auth/register.html")
        
        if "@" not in email:
            auth_logger.warning(f"Registration failed - invalid email for username: {username}")
            flash("Please enter a valid email address.", "error")
            return render_template("auth/register.html")
        
        # Validate company_id
        from config import get_enabled_companies
        try:
            enabled_companies = get_enabled_companies()
            if company_id not in enabled_companies:
                auth_logger.warning(f"Registration failed - invalid company {company_id} for username: {username}")
                flash("Invalid company selection.", "error")
                return render_template("auth/register.html", companies=enabled_companies)
        except Exception as e:
            log_error(e, "Failed to get enabled companies")
            # Fallback if config is not available
            if company_id not in ['haval', 'mg', 'kia']:
                company_id = 'haval'
                auth_logger.info(f"Fallback to default company 'haval' for username: {username}")
        
        # Create user
        user = User.create(username, email, password, company_id)
        if user:
            login_user(user)
            auth_logger.info(f"Successful registration and login for user: {username} (ID: {user.id})")
            log_user_action("Registration Success", user.id, f"Username: {username}, Company: {company_id}")
            flash(f"Welcome {user.username}! Your account has been created successfully.", "success")
            return redirect(url_for('chatbot_advanced'))
        else:
            auth_logger.warning(f"Registration failed - user already exists: username={username}, email={email}")
            flash("Username or email already exists. Please choose different ones.", "error")
    
    # Get available companies for the form
    try:
        from config import get_enabled_companies
        companies = get_enabled_companies()
        auth_logger.debug(f"Available companies loaded: {list(companies.keys())}")
    except Exception as e:
        log_error(e, "Failed to load companies for registration form")
        companies = {'haval': 'Haval', 'mg': 'MG', 'kia': 'Kia'}
    
    return render_template("auth/register.html", companies=companies)


@log_function_call(auth_logger)
def logout():
    """Handle user logout"""
    if current_user.is_authenticated:
        username = current_user.username
        user_id = current_user.id
        logout_user()
        auth_logger.info(f"User logged out: {username} (ID: {user_id})")
        log_user_action("Logout", user_id, f"Username: {username}")
        flash("You have been logged out.", "info")
    else:
        auth_logger.warning("Logout attempt by non-authenticated user")
    
    return redirect(url_for('login'))