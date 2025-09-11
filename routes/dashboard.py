from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from datetime import datetime, timedelta
import json

dashboard_bp = Blueprint('dashboard', __name__)

def refresh_current_user():
    """Refresh current_user object with latest data from database"""
    from app import db
    User = current_app.User
    
    try:
        # Get fresh user data from database
        user_from_db = User.query.get(current_user.id)
        if user_from_db:
            # Update all current_user attributes with fresh data
            current_user.email = user_from_db.email
            current_user.age = user_from_db.age
            current_user.gender = user_from_db.gender
            current_user.district = user_from_db.district
            current_user.block = user_from_db.block
            current_user.village = user_from_db.village
            current_user.pin_code = user_from_db.pin_code
            current_user.farm_size = user_from_db.farm_size
            current_user.primary_crops = user_from_db.primary_crops
            current_user.farming_experience = user_from_db.farming_experience
            current_user.farm_type = user_from_db.farm_type
            current_user.preferred_language = user_from_db.preferred_language
            current_user.notification_preferences = user_from_db.notification_preferences
            current_user.updated_at = user_from_db.updated_at
            current_user.created_at = user_from_db.created_at
            
            return True
    except Exception as e:
        print(f"Error refreshing current_user: {e}")
    
    return False

@dashboard_bp.route('/profile')
@login_required
def profile():
    """User profile dashboard"""
    from app import db
    
    # Get models from app context
    FarmerQuery = current_app.FarmerQuery
    User = current_app.User
    
    # Force database session to get fresh data
    db.session.expire_all()
    
    # Get fresh user data using the same method as the working test endpoints
    fresh_user = User.query.filter_by(id=current_user.id).first()
    if not fresh_user:
        flash('User not found', 'error')
        return redirect(url_for('auth.login'))
    
    # Debug: Print fresh user data
    print(f"DEBUG PROFILE: Fresh user email: {fresh_user.email}")
    print(f"DEBUG PROFILE: Fresh user age: {fresh_user.age}")
    print(f"DEBUG PROFILE: Fresh user district: {fresh_user.district}")
    print(f"DEBUG PROFILE: Fresh user farm_size: {fresh_user.farm_size}")
    print(f"DEBUG PROFILE: Fresh user profile completion: {fresh_user.get_profile_completion()}%")
    
    # Get user's recent queries using fresh_user.id
    recent_queries = FarmerQuery.query.filter_by(farmer_id=fresh_user.id)\
                                    .order_by(FarmerQuery.created_at.desc())\
                                    .limit(5).all()
    
    # Get query statistics using fresh_user.id
    total_queries = FarmerQuery.query.filter_by(farmer_id=fresh_user.id).count()
    answered_queries = FarmerQuery.query.filter_by(farmer_id=fresh_user.id, status='answered').count()
    pending_queries = FarmerQuery.query.filter_by(farmer_id=fresh_user.id, status='pending').count()
    
    # Calculate success rate
    success_rate = round((answered_queries / total_queries * 100) if total_queries > 0 else 0, 1)
    
    stats = {
        'total_queries': total_queries,
        'answered_queries': answered_queries,
        'pending_queries': pending_queries,
        'success_rate': success_rate
    }
    
    # Add cache-busting timestamp
    import time
    cache_buster = int(time.time())
    
    return render_template('dashboard/profile.html', 
                         user=fresh_user,  # Use fresh user data from database
                         recent_queries=recent_queries,
                         stats=stats,
                         cache_buster=cache_buster)

@dashboard_bp.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """Edit user profile"""
    if request.method == 'POST':
        from app import db
        User = current_app.User
        
        try:
            # Get the user object directly from database
            user_to_update = User.query.get(current_user.id)
            if not user_to_update:
                flash('User not found', 'error')
                return redirect(url_for('dashboard.profile'))
            
            # Debug: Print current state before update
            print(f"DEBUG EDIT: Before update - Email: {user_to_update.email}")
            print(f"DEBUG EDIT: Before update - Age: {user_to_update.age}")
            print(f"DEBUG EDIT: Before update - District: {user_to_update.district}")
            print(f"DEBUG EDIT: Before update - Farm Size: {user_to_update.farm_size}")
            print(f"DEBUG EDIT: Before update - Profile completion: {user_to_update.get_profile_completion()}%")
            
            # Update user information
            if request.form.get('full_name'):
                user_to_update.full_name = request.form.get('full_name').strip()
            if request.form.get('username'):
                user_to_update.username = request.form.get('username').strip()
            if request.form.get('phone'):
                user_to_update.phone = request.form.get('phone').strip()
            
            # Optional fields
            email = request.form.get('email', '').strip()
            user_to_update.email = email if email else None
            
            age = request.form.get('age', '').strip()
            user_to_update.age = int(age) if age and age.isdigit() else None
            
            gender = request.form.get('gender', '').strip()
            user_to_update.gender = gender if gender else None
            
            # Location information
            district = request.form.get('district', '').strip()
            user_to_update.district = district if district else None
            
            block = request.form.get('block', '').strip()
            user_to_update.block = block if block else None
            
            village = request.form.get('village', '').strip()
            user_to_update.village = village if village else None
            
            pin_code = request.form.get('pin_code', '').strip()
            user_to_update.pin_code = pin_code if pin_code else None
            
            # Farming information
            farm_size = request.form.get('farm_size', '').strip()
            user_to_update.farm_size = float(farm_size) if farm_size and farm_size.replace('.', '').isdigit() else None
            
            farming_experience = request.form.get('farming_experience', '').strip()
            user_to_update.farming_experience = int(farming_experience) if farming_experience and farming_experience.isdigit() else None
            
            farm_type = request.form.get('farm_type', '').strip()
            user_to_update.farm_type = farm_type if farm_type else None
            
            # Language preference
            user_to_update.preferred_language = request.form.get('preferred_language', 'ml')
            
            # Handle primary crops
            crops = request.form.getlist('primary_crops')
            if crops:
                user_to_update.primary_crops = json.dumps(crops)
            else:
                user_to_update.primary_crops = None
            
            # Update timestamp
            user_to_update.updated_at = datetime.utcnow()
            
            # Debug: Print what we're about to save
            print(f"DEBUG EDIT: About to save - Email: {user_to_update.email}")
            print(f"DEBUG EDIT: About to save - Age: {user_to_update.age}")
            print(f"DEBUG EDIT: About to save - District: {user_to_update.district}")
            print(f"DEBUG EDIT: About to save - Farm Size: {user_to_update.farm_size}")
            print(f"DEBUG EDIT: About to save - Profile completion: {user_to_update.get_profile_completion()}%")
            
            # Flush changes to database (without committing)
            db.session.flush()
            
            # Debug: Check state after flush but before commit
            print(f"DEBUG EDIT: After flush - Email: {user_to_update.email}")
            print(f"DEBUG EDIT: After flush - Age: {user_to_update.age}")
            print(f"DEBUG EDIT: After flush - District: {user_to_update.district}")
            print(f"DEBUG EDIT: After flush - Farm Size: {user_to_update.farm_size}")
            print(f"DEBUG EDIT: After flush - Profile completion: {user_to_update.get_profile_completion()}%")
            
            # Commit changes to database
            db.session.commit()
            
            # Debug: Verify what was actually saved
            fresh_check = User.query.get(current_user.id)
            print(f"DEBUG EDIT: After commit - Email: {fresh_check.email}")
            print(f"DEBUG EDIT: After commit - Age: {fresh_check.age}")
            print(f"DEBUG EDIT: After commit - District: {fresh_check.district}")
            print(f"DEBUG EDIT: After commit - Farm Size: {fresh_check.farm_size}")
            print(f"DEBUG EDIT: After commit - Profile completion: {fresh_check.get_profile_completion()}%")
            
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('dashboard.profile'))
            
        except ValueError as e:
            db.session.rollback()
            flash('Invalid data provided. Please check your input.', 'error')
        except Exception as e:
            db.session.rollback()
            flash('Error updating profile. Please try again.', 'error')
    
    # Get fresh user data directly from database
    User = current_app.User
    fresh_user = User.query.get(current_user.id)
    if not fresh_user:
        flash('User not found', 'error')
        return redirect(url_for('auth.login'))
    
    # Parse primary crops from JSON for form display
    primary_crops = []
    if fresh_user.primary_crops:
        try:
            primary_crops = json.loads(fresh_user.primary_crops)
        except (json.JSONDecodeError, TypeError):
            primary_crops = []
    
    return render_template('dashboard/edit_profile.html', user=fresh_user, primary_crops=primary_crops)

@dashboard_bp.route('/my-queries')
@login_required
def my_queries():
    """View user's queries and responses"""
    FarmerQuery = current_app.FarmerQuery
    
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    queries = FarmerQuery.query.filter_by(farmer_id=current_user.id)\
                              .order_by(FarmerQuery.created_at.desc())\
                              .paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('dashboard/my_queries.html', queries=queries)

@dashboard_bp.route('/query/<int:query_id>')
@login_required
def view_query(query_id):
    """View specific query and its responses"""
    FarmerQuery = current_app.FarmerQuery
    
    query = FarmerQuery.query.filter_by(id=query_id, farmer_id=current_user.id).first_or_404()
    
    return render_template('dashboard/view_query.html', query=query)

@dashboard_bp.route('/settings')
@login_required
def settings():
    """User settings page"""
    # Get fresh user data directly from database
    User = current_app.User
    fresh_user = User.query.get(current_user.id)
    if not fresh_user:
        flash('User not found', 'error')
        return redirect(url_for('auth.login'))
    
    # Parse notification preferences for template
    notification_prefs = {}
    if fresh_user.notification_preferences:
        try:
            notification_prefs = json.loads(fresh_user.notification_preferences)
        except (json.JSONDecodeError, TypeError):
            notification_prefs = {
                'email_notifications': True,
                'sms_notifications': True,
                'weather_alerts': True
            }
    else:
        notification_prefs = {
            'email_notifications': True,
            'sms_notifications': True,
            'weather_alerts': True
        }
    
    return render_template('dashboard/settings.html', user=fresh_user, notification_prefs=notification_prefs)

@dashboard_bp.route('/update-settings', methods=['POST'])
@login_required
def update_settings():
    """Update user settings like language preference"""
    from app import db
    User = current_app.User
    
    try:
        # Get language preference
        preferred_language = request.form.get('preferred_language', 'ml')
        
        # Validate language preference
        if preferred_language not in ['ml', 'en']:
            preferred_language = 'ml'
        
        # Update user settings
        current_user.preferred_language = preferred_language
        current_user.updated_at = datetime.utcnow()
        
        # Commit changes
        db.session.commit()
        
        # Refresh current_user with updated data
        refresh_current_user()
        
        flash('Language preference updated successfully!', 'success')
        print(f"Language preference updated for user {current_user.username}: {preferred_language}")
        
    except Exception as e:
        db.session.rollback()
        flash('Error updating language preference. Please try again.', 'error')
        print(f"Settings update error: {e}")
    
    return redirect(url_for('dashboard.settings'))

@dashboard_bp.route('/update-notifications', methods=['POST'])
@login_required
def update_notifications():
    """Update notification settings"""
    from app import db
    User = current_app.User
    
    try:
        # Get notification preferences
        email_notifications = request.form.get('email_notifications') == 'on'
        sms_notifications = request.form.get('sms_notifications') == 'on'
        weather_alerts = request.form.get('weather_alerts') == 'on'
        
        # Store notification preferences as JSON in a single field
        # Since we don't have separate fields, we'll store them in a JSON format
        notification_preferences = {
            'email_notifications': email_notifications,
            'sms_notifications': sms_notifications,
            'weather_alerts': weather_alerts
        }
        
        # Store notification preferences in the new notification_preferences field
        current_user.notification_preferences = json.dumps(notification_preferences)
        
        # Update timestamp
        current_user.updated_at = datetime.utcnow()
        
        # Commit changes
        db.session.commit()
        
        # Refresh current_user with updated data
        refresh_current_user()
        
        flash('Notification settings updated successfully!', 'success')
        print(f"Notification settings updated for user {current_user.username}: {notification_preferences}")
        
    except Exception as e:
        db.session.rollback()
        flash('Error updating notification settings. Please try again.', 'error')
        print(f"Notification update error: {e}")
    
    return redirect(url_for('dashboard.settings'))

@dashboard_bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    """Change user password"""
    from app import db
    User = current_app.User
    
    current_password = request.form.get('current_password', '')
    new_password = request.form.get('new_password', '')
    confirm_password = request.form.get('confirm_password', '')
    
    # Validation
    if not current_password:
        flash('Current password is required', 'error')
        return redirect(url_for('dashboard.settings'))
    
    if not current_user.check_password(current_password):
        flash('Current password is incorrect', 'error')
        return redirect(url_for('dashboard.settings'))
    
    if len(new_password) < 6:
        flash('New password must be at least 6 characters long', 'error')
        return redirect(url_for('dashboard.settings'))
    
    if new_password != confirm_password:
        flash('New passwords do not match', 'error')
        return redirect(url_for('dashboard.settings'))
    
    # Update password
    try:
        current_user.set_password(new_password)
        current_user.updated_at = datetime.utcnow()
        db.session.commit()
        
        # Refresh current_user with updated data
        refresh_current_user()
        
        flash('Password changed successfully!', 'success')
        print(f"Password changed for user {current_user.username}")
    except Exception as e:
        db.session.rollback()
        flash('Error changing password. Please try again.', 'error')
        print(f"Password change error: {e}")
    
    return redirect(url_for('dashboard.settings'))

@dashboard_bp.route('/api/profile-completion')
@login_required
def api_profile_completion():
    """API endpoint to get profile completion percentage"""
    return jsonify({
        'completion': current_user.get_profile_completion(),
        'user_data': current_user.to_dict()
    })

@dashboard_bp.route('/debug-profile')
@login_required
def debug_profile():
    """Debug endpoint to check user profile data"""
    from app import db
    
    # Get fresh user data directly from database
    User = current_app.User
    user_from_db = User.query.get(current_user.id)
    
    # Force refresh current_user
    refresh_current_user()
    
    debug_info = {
        'current_user_id': current_user.id,
        'current_user_username': current_user.username,
        'current_user_email': current_user.email,
        'current_user_age': current_user.age,
        'current_user_district': current_user.district,
        'current_user_farm_size': current_user.farm_size,
        'current_user_primary_crops': current_user.primary_crops,
        'current_user_updated_at': current_user.updated_at.isoformat() if current_user.updated_at else None,
        'profile_completion': current_user.get_profile_completion(),
        'db_user_email': user_from_db.email if user_from_db else None,
        'db_user_age': user_from_db.age if user_from_db else None,
        'db_user_district': user_from_db.district if user_from_db else None,
        'db_user_farm_size': user_from_db.farm_size if user_from_db else None,
        'db_user_primary_crops': user_from_db.primary_crops if user_from_db else None,
        'db_user_updated_at': user_from_db.updated_at.isoformat() if user_from_db and user_from_db.updated_at else None,
        'data_sync_status': 'SYNCED' if (current_user.email == user_from_db.email if user_from_db else False) else 'OUT_OF_SYNC',
        'fresh_user_profile_completion': user_from_db.get_profile_completion() if user_from_db else None
    }
    
    return jsonify(debug_info)

@dashboard_bp.route('/debug-database')
@login_required
def debug_database():
    """Debug endpoint to check raw database data"""
    from app import db
    import sqlite3
    
    try:
        # Connect directly to SQLite database
        db_path = "instance/farmer_support.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get raw user data from database
        cursor.execute("SELECT * FROM users WHERE id = ?", (current_user.id,))
        user_row = cursor.fetchone()
        
        # Get column names
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        conn.close()
        
        if user_row:
            # Create dictionary from row data
            user_data = dict(zip(columns, user_row))
            return jsonify({
                'status': 'success',
                'user_id': current_user.id,
                'raw_database_data': user_data,
                'columns': columns
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'User not found in database'
            })
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        })

@dashboard_bp.route('/test-db-update')
@login_required
def test_db_update():
    """Test endpoint to verify database updates work"""
    from app import db
    User = current_app.User
    
    try:
        # Get current user data
        user = User.query.get(current_user.id)
        if not user:
            return jsonify({'status': 'error', 'message': 'User not found'})
        
        # Update test data
        user.email = 'test@example.com'
        user.age = 35
        user.district = 'Ernakulam'
        user.village = 'Chendamangalam'
        user.farm_size = 2.5
        user.farming_experience = 10
        user.updated_at = datetime.utcnow()
        
        # Commit to database
        db.session.commit()
        
        # Verify by querying fresh data
        fresh_user = User.query.get(current_user.id)
        
        return jsonify({
            'status': 'success',
            'user_id': current_user.id,
            'updated_data': {
                'email': fresh_user.email,
                'age': fresh_user.age,
                'district': fresh_user.district,
                'village': fresh_user.village,
                'farm_size': fresh_user.farm_size,
                'farming_experience': fresh_user.farming_experience
            },
            'profile_completion': fresh_user.get_profile_completion()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': str(e)
        })

@dashboard_bp.route('/test-profile-update')
@login_required
def test_profile_update():
    """Test endpoint to simulate profile update and check results"""
    from app import db
    User = current_app.User
    
    try:
        # Get current user data
        user = User.query.get(current_user.id)
        if not user:
            return jsonify({'status': 'error', 'message': 'User not found'})
        
        # Store original data
        original_data = {
            'email': user.email,
            'age': user.age,
            'district': user.district,
            'village': user.village,
            'farm_size': user.farm_size,
            'farming_experience': user.farming_experience,
            'profile_completion': user.get_profile_completion()
        }
        
        # Update with test data
        user.email = 'test_profile@example.com'
        user.age = 40
        user.district = 'Thrissur'
        user.village = 'Kodungallur'
        user.farm_size = 3.5
        user.farming_experience = 15
        user.updated_at = datetime.utcnow()
        
        # Force flush and commit
        db.session.flush()
        db.session.commit()
        
        # Force session refresh to ensure data is persisted
        db.session.expire_all()
        
        # Get fresh data after commit using a new query
        fresh_user = User.query.filter_by(id=current_user.id).first()
        
        # Get profile data for template rendering
        fresh_data = {
            'email': fresh_user.email,
            'age': fresh_user.age,
            'district': fresh_user.district,
            'village': fresh_user.village,
            'farm_size': fresh_user.farm_size,
            'farming_experience': fresh_user.farming_experience,
            'profile_completion': fresh_user.get_profile_completion()
        }
        
        return jsonify({
            'status': 'success',
            'user_id': current_user.id,
            'original_data': original_data,
            'fresh_data_after_update': fresh_data,
            'data_changed': original_data != fresh_data,
            'profile_completion_increased': fresh_data['profile_completion'] > original_data['profile_completion']
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': str(e)
        })

@dashboard_bp.route('/profile-data')
@login_required
def profile_data():
    """API endpoint to get current profile data for debugging"""
    from app import db
    User = current_app.User
    
    # Force database session refresh
    db.session.expire_all()
    
    # Get fresh user data
    fresh_user = User.query.filter_by(id=current_user.id).first()
    if not fresh_user:
        return jsonify({'status': 'error', 'message': 'User not found'})
    
    return jsonify({
        'status': 'success',
        'user_id': current_user.id,
        'profile_data': {
            'email': fresh_user.email,
            'age': fresh_user.age,
            'district': fresh_user.district,
            'village': fresh_user.village,
            'farm_size': fresh_user.farm_size,
            'farming_experience': fresh_user.farming_experience,
            'profile_completion': fresh_user.get_profile_completion()
        },
        'timestamp': datetime.utcnow().isoformat()
    })

@dashboard_bp.route('/test-profile-route')
@login_required
def test_profile_route():
    """Test endpoint to verify profile route logic"""
    from app import db
    User = current_app.User
    
    try:
        # Use the exact same approach as the profile route
        db.session.expire_all()
        
        # Get fresh user data using the same method as the profile route
        fresh_user = User.query.filter_by(id=current_user.id).first()
        if not fresh_user:
            return jsonify({'status': 'error', 'message': 'User not found'})
        
        return jsonify({
            'status': 'success',
            'user_id': current_user.id,
            'profile_data': {
                'email': fresh_user.email,
                'age': fresh_user.age,
                'district': fresh_user.district,
                'village': fresh_user.village,
                'farm_size': fresh_user.farm_size,
                'farming_experience': fresh_user.farming_experience,
                'profile_completion': fresh_user.get_profile_completion()
            },
            'timestamp': datetime.utcnow().isoformat()
        })
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        })

@dashboard_bp.route('/manual-profile-update')
@login_required
def manual_profile_update():
    """Manual endpoint to update profile data and ensure persistence"""
    from app import db
    User = current_app.User
    
    try:
        # Get current user data
        user = User.query.get(current_user.id)
        if not user:
            return jsonify({'status': 'error', 'message': 'User not found'})
        
        # Update with specific test data
        user.email = 'manual_test@example.com'
        user.age = 45
        user.district = 'Kochi'
        user.village = 'Fort Kochi'
        user.farm_size = 5.0
        user.farming_experience = 20
        user.updated_at = datetime.utcnow()
        
        # Force commit
        db.session.commit()
        
        # Verify the update by querying fresh data
        fresh_user = User.query.filter_by(id=current_user.id).first()
        
        return jsonify({
            'status': 'success',
            'message': 'Profile updated manually',
            'user_id': current_user.id,
            'updated_data': {
                'email': fresh_user.email,
                'age': fresh_user.age,
                'district': fresh_user.district,
                'village': fresh_user.village,
                'farm_size': fresh_user.farm_size,
                'farming_experience': fresh_user.farming_experience,
                'profile_completion': fresh_user.get_profile_completion()
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': str(e)
        })