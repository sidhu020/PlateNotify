# app.py
"""Main Flask application for PlateNotify.

Provides user authentication, vehicle registration, anonymous reporting, and a dashboard.
The application now uses a dedicated configuration module, rate limiting, security headers,
and structured logging to meet production‑grade standards while maintaining a student‑friendly
codebase.
"""

import os
import click
import logging
from datetime import datetime
from flask import Flask, render_template, redirect, url_for, flash, request, abort
from flask_wtf.csrf import CSRFProtect
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

# I'm importing email-validator and my custom helpers here!
# Gemini said using email-validator is way safer than my silly '@' and '.' check.
# Also safe_redirect prevents hackers from doing malicious redirects.
from email_validator import validate_email, EmailNotValidError
from helpers import safe_redirect, format_datetime, send_telegram_message

# Load configuration (development or production)
# Gemini told me FLASK_ENV is deprecated in newer Flask versions!
# So I checked FLASK_DEBUG too, or default to development if it's not set.
if os.getenv('FLASK_ENV') == 'production' or os.getenv('FLASK_DEBUG') == '0':
    from config import ProductionConfig as Config
else:
    from config import DevelopmentConfig as Config

# Initialise Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Configure basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info('PlateNotify app initializing')

# Initialise extensions (db, login_manager, limiter, talisman)
from extensions import db, login_manager, limiter, talisman

# Security: CSRF protection and HTTP headers
csrf = CSRFProtect(app)
# Flask‑Talisman will apply CSP, HSTS, etc.

# Talisman forces HTTPS by default, which broke my local testing because Flask
# doesn't run SSL on localhost:5000! Gemini told me to set force_https to False
# when we are in debug mode. Super helpful!
#
# Also, wait! Gemini pointed out that Talisman doesn't automatically load the
# TALISMAN_CONTENT_SECURITY_POLICY or TALISMAN_PERMISSION_POLICY from config.py!
# That's why my Bootstrap CSS and JS were blocked by the default-src 'self' rule.
# I need to pass them explicitly so the browser allows the CDN!
talisman.init_app(
    app,
    force_https=not app.config.get('DEBUG', False),
    content_security_policy=app.config.get('TALISMAN_CONTENT_SECURITY_POLICY'),
    feature_policy=app.config.get('TALISMAN_PERMISSION_POLICY'),
    permissions_policy=app.config.get('TALISMAN_PERMISSIONS_POLICY')
)

# Ensure the SQLite instance folder exists
os.makedirs(app.instance_path, exist_ok=True)

# Attach extensions to the app
db.init_app(app)
login_manager.init_app(app)
limiter.init_app(app)

login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'

# Import models after DB is set up to avoid circular imports
from models import User, Vehicle, Report

# User loader for Flask‑Login
@login_manager.user_loader
def load_user(user_id):
    # Gemini said using User.query.get() is deprecated in SQLAlchemy 2.0!
    # I should use db.session.get() instead.
    try:
        return db.session.get(User, int(user_id))
    except (ValueError, TypeError):
        return None

# ---------- Routes ----------

@app.route('/')
def index():
    return render_template('index.html')

# ----- Authentication -----
@limiter.limit('5 per minute')
@app.route('/register', methods=['GET', 'POST'])
def register():
    """Handle user registration with validation."""
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()

        # Basic validation
        if not email or not password:
            flash('Email and password are required.', 'danger')
            return safe_redirect('register')
        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'danger')
            return safe_redirect('register')
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return safe_redirect('register')
        
        # Checking if email is valid using the email-validator library
        # This was super tricky because I had to handle EmailNotValidError!
        try:
            valid_email = validate_email(email)
            email = valid_email.normalized
        except EmailNotValidError as e:
            flash(f'Invalid email address: {str(e)}', 'danger')
            return safe_redirect('register')

        if User.query.filter_by(email=email).first():
            flash('Email already registered. Try logging in instead.', 'warning')
            return safe_redirect('login')

        # Create the user
        try:
            user = User(email=email, password_hash=generate_password_hash(password))
            db.session.add(user)
            db.session.commit()
            flash('Registration successful! Please log in.', 'success')
            return safe_redirect('login')
        except Exception as e:
            db.session.rollback()
            logger.exception('Registration error')
            flash('An error occurred. Please try again.', 'danger')
            return safe_redirect('register')
    return render_template('register.html')

@limiter.limit('5 per minute')
@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login authentication."""
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()

        if not email or not password:
            flash('Email and password are required.', 'danger')
            return safe_redirect('login')

        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            flash(f'Welcome back, {user.email.split("@")[0]}!', 'success')
            return safe_redirect('dashboard')
        flash('Invalid email or password. Please try again.', 'danger')
        return safe_redirect('login')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    """Handle user logout."""
    logout_user()
    flash('You have been logged out. Goodbye!', 'info')
    return safe_redirect('index')

# ----- Dashboard -----
@app.route('/dashboard')
@login_required
def dashboard():
    """Display user dashboard with vehicles and reports."""
    vehicles = Vehicle.query.filter_by(user_id=current_user.id).all()
    unread_count = Report.query.join(Vehicle).filter(
        Vehicle.user_id == current_user.id,
        Report.is_read == False
    ).count()
    all_reports = Report.query.join(Vehicle).filter(
        Vehicle.user_id == current_user.id
    ).order_by(Report.created_at.desc()).all()
    return render_template('dashboard.html', vehicles=vehicles,
                           unread_count=unread_count, all_reports=all_reports)


@app.route('/telegram/setup', methods=['POST'])
@login_required
def setup_telegram():
    """Save or update the user's Telegram Chat ID."""
    # We get the chat ID from the form and strip whitespaces
    chat_id = request.form.get('telegram_chat_id', '').strip()
    
    # Simple validation: Telegram chat IDs are just long numbers (e.g. 562948291).
    # If they put letters, we flash a friendly error!
    if chat_id and not chat_id.isdigit():
        flash('Invalid Chat ID. A Telegram Chat ID should contain numbers only.', 'danger')
        return safe_redirect('dashboard')
        
    try:
        # Save it to the user object (it can be empty if they want to turn off alerts)
        current_user.telegram_chat_id = chat_id or None
        db.session.commit()
        if chat_id:
            flash('✓ Telegram notifications enabled! Try submitting an anonymous report for one of your plates to test it.', 'success')
        else:
            flash('Telegram notifications disabled.', 'info')
    except Exception as e:
        db.session.rollback()
        logger.exception('Telegram setup error')
        flash('An error occurred while saving your Telegram Chat ID.', 'danger')
        
    return safe_redirect('dashboard')


# ----- Vehicle Management -----
@app.route('/vehicle/add', methods=['GET', 'POST'])
@login_required
def add_vehicle():
    """Add a new vehicle to the user's account."""
    if request.method == 'POST':
        plate = request.form.get('plate_number', '').strip().upper()
        if not plate:
            flash('Please enter a license plate number.', 'danger')
            return safe_redirect('add_vehicle')
        if len(plate) < 2 or len(plate) > 10:
            flash('License plate should be between 2 and 10 characters.', 'danger')
            return safe_redirect('add_vehicle')
            
        # I changed this because plate_number is now unique globally!
        # If someone else registered this plate, we can't let another user add it.
        # Otherwise, database goes boom (UniqueConstraint fails)!
        if Vehicle.query.filter_by(plate_number=plate).first():
            flash('This license plate is already registered by another user.', 'warning')
            return safe_redirect('dashboard')
            
        try:
            vehicle = Vehicle(user_id=current_user.id, plate_number=plate)
            db.session.add(vehicle)
            db.session.commit()
            flash(f'✓ Vehicle {plate} added successfully!', 'success')
            return safe_redirect('dashboard')
        except Exception as e:
            db.session.rollback()
            logger.exception('Add vehicle error')
            flash('An error occurred while adding the vehicle.', 'danger')
            return safe_redirect('add_vehicle')
    return render_template('add_vehicle.html')

@app.route('/vehicle/delete/<int:vehicle_id>', methods=['POST'])
@login_required
def delete_vehicle(vehicle_id):
    """Delete a vehicle from the user's account."""
    # Gemini said using Vehicle.query.get_or_404 is old-fashioned and deprecated.
    # So I replaced it with the modern db.get_or_404. Much cleaner!
    vehicle = db.get_or_404(Vehicle, vehicle_id)
    if vehicle.user_id != current_user.id:
        abort(403)
    try:
        plate = vehicle.plate_number
        db.session.delete(vehicle)
        db.session.commit()
        flash(f'Vehicle {plate} has been deleted.', 'info')
    except Exception as e:
        db.session.rollback()
        logger.exception('Delete vehicle error')
        flash('An error occurred while deleting the vehicle.', 'danger')
    return safe_redirect('dashboard')

# ----- Anonymous Reporting -----
@app.route('/report', methods=['GET', 'POST'])
def report():
    """Submit an anonymous report about a vehicle."""
    issues = [
        'Headlights on', 'Bad parking', 'Blocking another vehicle',
        'Alarm ringing', 'Window open', 'Blocking fire zone',
        'Excessive noise', 'Other'
    ]
    if request.method == 'POST':
        plate = request.form.get('plate_number', '').strip().upper()
        issue_type = request.form.get('issue_type', '').strip()
        message = request.form.get('message', '').strip()

        if not plate or not issue_type:
            flash('Please enter a plate number and select an issue type.', 'danger')
            return safe_redirect('report')
        if len(plate) < 2 or len(plate) > 10:
            flash('Please enter a valid license plate.', 'danger')
            return safe_redirect('report')
        if issue_type not in issues:
            flash('Please select a valid issue type.', 'danger')
            return safe_redirect('report')
        if len(message) > 500:
            flash('Message is too long (max 500 characters).', 'danger')
            return safe_redirect('report')

        vehicle = Vehicle.query.filter_by(plate_number=plate).first()
        if not vehicle:
            # SECURITY STUFF: Gemini explained that showing "Plate not registered"
            # leaks user accounts/plates information (user enumeration vulnerability).
            # So I will return a success message anyway so hackers don't know if the car is registered!
            # It's a fake success but it keeps the data safe!
            flash('Thank you! Your anonymous report has been submitted.', 'success')
            return safe_redirect('report')
        try:
            new_report = Report(vehicle_id=vehicle.id, issue_type=issue_type,
                               message=message or None)
            db.session.add(new_report)
            db.session.commit()

            # --- Telegram Notification ---
            # If the vehicle owner has set up Telegram and the bot is configured, send them an alert!
            # Gemini said it's cool to do this after committing the report so the data is saved first!
            token = app.config.get('TELEGRAM_BOT_TOKEN')
            chat_id = vehicle.owner.telegram_chat_id
            if token and chat_id:
                tele_msg = (
                    f"<b>🚗 PlateNotify Alert!</b>\n\n"
                    f"Someone reported an issue with your vehicle <b>{plate}</b>.\n"
                    f"• <b>Issue:</b> {issue_type}\n"
                )
                if message:
                    tele_msg += f"• <b>Details:</b> <i>{message}</i>\n"
                tele_msg += f"\nCheck your <a href='{request.host_url}dashboard'>PlateNotify Dashboard</a> for details."
                
                send_telegram_message(token, chat_id, tele_msg)

            flash('Thank you! Your anonymous report has been submitted.', 'success')
            return safe_redirect('report')
        except Exception as e:
            db.session.rollback()
            logger.exception('Report submission error')
            flash('An error occurred while submitting the report.', 'danger')
            return safe_redirect('report')
    return render_template('report.html', issues=issues)

# ----- Report Management -----
@app.route('/report/<int:report_id>/mark-read', methods=['POST'])
@login_required
def mark_read(report_id):
    """Mark a report as read."""
    # Using modern db.get_or_404 here too!
    report = db.get_or_404(Report, report_id)
    if report.vehicle.owner.id != current_user.id:
        abort(403)
    try:
        report.is_read = True
        db.session.commit()
        flash('Report marked as read.', 'info')
    except Exception as e:
        db.session.rollback()
        logger.exception('Mark read error')
        flash('An error occurred. Please try again.', 'danger')
    return safe_redirect('dashboard')

@app.route('/report/<int:report_id>/delete', methods=['POST'])
@login_required
def delete_report(report_id):
    """Delete a report."""
    # Using modern db.get_or_404 here too!
    report = db.get_or_404(Report, report_id)
    if report.vehicle.owner.id != current_user.id:
        abort(403)
    try:
        db.session.delete(report)
        db.session.commit()
        flash('Report has been deleted.', 'info')
    except Exception as e:
        db.session.rollback()
        logger.exception('Delete report error')
        flash('An error occurred while deleting the report.', 'danger')
    return safe_redirect('dashboard')

# ----- Error Handlers -----
@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(403)
def forbidden(error):
    flash('You do not have permission to access this resource.', 'danger')
    return safe_redirect('dashboard'), 403

@app.errorhandler(500)
def server_error(error):
    db.session.rollback()
    flash('An unexpected error occurred. Please try again.', 'danger')
    return safe_redirect('index'), 500

# ----- CLI Commands -----
@app.cli.command('init-db')
def init_db_command():
    """Create database tables."""
    with app.app_context():
        os.makedirs(app.instance_path, exist_ok=True)
        db.create_all()
    click.echo('Initialized the database.')

if __name__ == '__main__':
    # Run the application (debug mode is controlled by the configuration)
    app.run(host='0.0.0.0', port=5000)

