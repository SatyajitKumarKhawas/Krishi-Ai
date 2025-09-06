from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from datetime import datetime, timedelta
import json

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/profile')
@login_required
def profile():
    """User profile dashboard"""
    # Get models from app context - FIXED DATABASE ACCESS
    from app import db
    FarmerQuery = current_app.FarmerQuery
    
    # Get user's recent queries
    recent_queries = FarmerQuery.query.filter_by(farmer_id=current_user.id)\
                                    .order_by(FarmerQuery.created_at.desc())\
                                    .limit(5).all()
    
    # Get query statistics
    total_queries = FarmerQuery.query.filter_by(farmer_id=current_user.id).count()
    answered_queries = FarmerQuery.query.filter_by(farmer_id=current_user.id, status='answered').count()
    pending_queries = FarmerQuery.query.filter_by(farmer_id=current_user.id, status='pending').count()
    
    # Calculate success rate
    success_rate = round((answered_queries / total_queries * 100) if total_queries > 0 else 0, 1)
    
    stats = {
        'total_queries': total_queries,
        'answered_queries': answered_queries,
        'pending_queries': pending_queries,
        'success_rate': success_rate
    }
    
    return render_template('dashboard/profile.html', 
                         user=current_user, 
                         recent_queries=recent_queries,
                         stats=stats)

@dashboard_bp.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """Edit user profile"""
    if request.method == 'POST':
        from app import db
        
        # Update user information
        current_user.email = request.form.get('email', '').strip() or None
        current_user.age = int(request.form.get('age')) if request.form.get('age') else None
        current_user.gender = request.form.get('gender', '').strip() or None
        current_user.district = request.form.get('district', '').strip() or None
        current_user.block = request.form.get('block', '').strip() or None
        current_user.village = request.form.get('village', '').strip() or None
        current_user.pin_code = request.form.get('pin_code', '').strip() or None
        current_user.farm_size = float(request.form.get('farm_size')) if request.form.get('farm_size') else None
        current_user.farming_experience = int(request.form.get('farming_experience')) if request.form.get('farming_experience') else None
        current_user.farm_type = request.form.get('farm_type', '').strip() or None
        current_user.preferred_language = request.form.get('preferred_language', 'ml')
        
        # Handle primary crops (convert list to JSON string)
        crops = request.form.getlist('primary_crops')
        if crops:
            current_user.primary_crops = json.dumps(crops)
        
        current_user.updated_at = datetime.utcnow()
        
        try:
            db.session.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('dashboard.profile'))
        except Exception as e:
            db.session.rollback()
            flash('Error updating profile. Please try again.', 'error')
            print(f"Profile update error: {e}")
    
    # Parse primary crops from JSON for form display
    primary_crops = []
    if current_user.primary_crops:
        try:
            primary_crops = json.loads(current_user.primary_crops)
        except:
            pass
    
    return render_template('dashboard/edit_profile.html', user=current_user, primary_crops=primary_crops)

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
    return render_template('dashboard/settings.html', user=current_user)

@dashboard_bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    """Change user password"""
    from app import db
    
    current_password = request.form.get('current_password', '')
    new_password = request.form.get('new_password', '')
    confirm_password = request.form.get('confirm_password', '')
    
    # Validation
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
        flash('Password changed successfully!', 'success')
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