from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import current_user, login_user, logout_user, login_required
import re

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Farmer registration page"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.profile'))

    if request.method == 'POST':
        User = current_app.User  # Use model from app context
        db = current_app.extensions['sqlalchemy'].db  # Get db instance

        username = request.form.get('username', '').strip()
        phone = request.form.get('phone', '').strip()
        full_name = request.form.get('full_name', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        email = request.form.get('email', '').strip() or None
        preferred_language = request.form.get('preferred_language', 'ml')

        errors = []

        if not username or len(username) < 3:
            errors.append('Username must be at least 3 characters long')

        if not phone or not re.match(r'^[6-9]\d{9}$', phone):
            errors.append('Please enter a valid 10-digit mobile number')

        if not full_name:
            errors.append('Full name is required')

        if not password or len(password) < 6:
            errors.append('Password must be at least 6 characters long')

        if password != confirm_password:
            errors.append('Passwords do not match')

        if email and not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email):
            errors.append('Please enter a valid email address')

        if User.query.filter_by(username=username).first():
            errors.append('Username already exists')

        if User.query.filter_by(phone=phone).first():
            errors.append('Phone number already registered')

        if email and User.query.filter_by(email=email).first():
            errors.append('Email already registered')

        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('auth/register.html')

        try:
            user = User(username=username, phone=phone, full_name=full_name, password=password)
            user.email = email
            user.preferred_language = preferred_language

            db.session.add(user)
            db.session.commit()

            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('auth.login'))

        except Exception as e:
            db.session.rollback()
            flash('Registration failed. Please try again.', 'error')
            print(f"Registration error: {e}")

    return render_template('auth/register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Farmer login page"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.profile'))

    if request.method == 'POST':
        User = current_app.User  # Model from app context
        db = current_app.extensions['sqlalchemy'].db

        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember = request.form.get('remember', False)

        if not username or not password:
            flash('Please enter both username and password', 'error')
            return render_template('auth/login.html')

        user = User.query.filter(
            (User.username == username) | (User.phone == username)
        ).first()

        if user and user.check_password(password):
            if user.is_active:
                login_user(user, remember=remember)
                user.update_last_login()
                db.session.commit()

                next_page = request.args.get('next')
                if next_page:
                    return redirect(next_page)
                return redirect(url_for('dashboard.profile'))
            else:
                flash('Your account has been deactivated. Please contact support.', 'error')
        else:
            flash('Invalid username/phone or password', 'error')

    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully', 'success')
    return redirect(url_for('index'))


@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        User = current_app.User
        phone = request.form.get('phone', '').strip()

        if not phone:
            flash('Please enter your phone number', 'error')
            return render_template('auth/forgot_password.html')

        user = User.query.filter_by(phone=phone).first()
        if user:
            flash('Password reset instructions have been sent to your phone', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash('No account found with this phone number', 'error')

    return render_template('auth/forgot_password.html')
