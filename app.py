from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, timezone
import re
from markupsafe import Markup
try:
    from zoneinfo import ZoneInfo
except Exception:
    ZoneInfo = None
import os
from config import config

# Initialize Flask app
app = Flask(__name__)

# Load configuration
env = os.environ.get('FLASK_ENV', 'development')
app.config.from_object(config.get(env, 'default'))

# Initialize extensions
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'

# Create models using factory functions - CREATE ONCE HERE
from models.user import create_user_model
from models.query import create_farmer_query_model
from models.response import create_query_response_model

User = create_user_model(db)
FarmerQuery = create_farmer_query_model(db)
QueryResponse = create_query_response_model(db)

# Make models available globally
app.User = User
app.FarmerQuery = FarmerQuery
app.QueryResponse = QueryResponse

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    """Home page route"""
    return render_template('index.html')

@app.route('/about')
def about():
    """About page route"""
    return render_template('about.html')

@app.route('/services')
def services():
    """Services page route"""
    return render_template('services.html')

@app.route('/contact')
def contact():
    """Contact page route"""
    return render_template('contact.html')

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)  
def internal_error(error):
    db.session.rollback()
    return render_template('errors/500.html'), 500

# Utility functions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Context processors
@app.context_processor
def inject_models():
    """Make models available in templates"""
    return {
        'User': User,
        'FarmerQuery': FarmerQuery,
        'QueryResponse': QueryResponse
    }

# Jinja filters
def format_dt_local(dt, fmt='%d %b %Y at %I:%M %p'):
    """Format UTC datetime to Asia/Kolkata local time for display."""
    if not dt:
        return ''
    try:
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        if ZoneInfo is not None:
            dt_local = dt.astimezone(ZoneInfo('Asia/Kolkata'))
        else:
            # Fallback: IST is UTC+5:30 (no DST); approximate if zoneinfo unavailable
            dt_local = dt.astimezone()
        return dt_local.strftime(fmt)
    except Exception:
        return dt.strftime(fmt)

app.jinja_env.filters['format_dt_local'] = format_dt_local

def format_ai_response(text: str) -> Markup:
    """Convert AI response markdown-ish text to clean HTML for readability.

    - Remove stray ** markers
    - Bold section titles like "1) Direct Answer:" or "Safety:"
    - Convert bullet points (*, -) to <ul><li>
    - Convert ordered points (1., 2.) to <ol><li>
    - Preserve paragraphs
    """
    if not text:
        return Markup("")

    # Normalize newlines and strip asterisks used for emphasis
    cleaned = text.replace("**", "").replace("\r\n", "\n").replace("\r", "\n")
    lines = cleaned.split("\n")

    html_parts = []
    in_ul = False
    in_ol = False

    def close_lists():
        nonlocal in_ul, in_ol
        if in_ul:
            html_parts.append("</ul>")
            in_ul = False
        if in_ol:
            html_parts.append("</ol>")
            in_ol = False

    section_re = re.compile(r"^\s*(?:\d+\)\s*)?([^:]{3,}?):\s*$")
    bullet_re = re.compile(r"^\s*([*-])\s+(.*)$")
    ordered_re = re.compile(r"^\s*(\d+)\.\s+(.*)$")

    for raw in lines:
        line = raw.strip()
        if not line:
            close_lists()
            html_parts.append("<br>")
            continue

        m_sec = section_re.match(line)
        if m_sec:
            close_lists()
            title = m_sec.group(1).strip()
            # Replace "Direct Answer" with just "Answer"
            if re.match(r"^direct\s+answer$", title, flags=re.IGNORECASE):
                title = "Answer"
            html_parts.append(f"<div class=\"ai-section-title\"><strong>{title}:</strong></div>")
            continue

        m_b = bullet_re.match(line)
        if m_b:
            if not in_ul:
                close_lists()
                html_parts.append("<ul class=\"ai-list\">")
                in_ul = True
            html_parts.append(f"<li>{m_b.group(2).strip()}</li>")
            continue

        m_o = ordered_re.match(line)
        if m_o:
            if not in_ol:
                close_lists()
                html_parts.append("<ol class=\"ai-olist\">")
                in_ol = True
            html_parts.append(f"<li>{m_o.group(2).strip()}</li>")
            continue

        # Regular paragraph line
        close_lists()
        html_parts.append(f"<span class=\"ai-line\">{line}</span>")

    close_lists()
    html = "\n".join(html_parts)
    return Markup(html)

app.jinja_env.filters['format_ai_response'] = format_ai_response

# Import and register routes AFTER creating models
from routes.auth import auth_bp
from routes.dashboard import dashboard_bp  
from routes.query import query_bp

app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
app.register_blueprint(query_bp, url_prefix='/query')

if __name__ == '__main__':
    # Create upload folder if it doesn't exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Create database tables
    with app.app_context():
        db.create_all()
        print("✅ Database tables created successfully!")
    
    print("🌾 Kerala Krishi AI - Starting server...")
    print("🔗 Access the application at: http://localhost:5000")
    print("📱 Mobile view available at: http://your-ip:5000")
    
    app.run(debug=True, host='0.0.0.0', port=5000)