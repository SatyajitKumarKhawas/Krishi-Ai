from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

def create_user_model(db):
    """Factory function to create User model with db instance"""
    
    class User(UserMixin, db.Model):
        """User model for farmer registration and authentication"""
        __tablename__ = 'users'
        
        id = db.Column(db.Integer, primary_key=True)
        
        # Basic Information
        username = db.Column(db.String(80), unique=True, nullable=False)
        email = db.Column(db.String(120), unique=True, nullable=True)
        phone = db.Column(db.String(15), unique=True, nullable=False)
        password_hash = db.Column(db.String(128), nullable=False)
        
        # Personal Information
        full_name = db.Column(db.String(100), nullable=False)
        age = db.Column(db.Integer, nullable=True)
        gender = db.Column(db.String(10), nullable=True)
        
        # Location Information
        district = db.Column(db.String(50), nullable=True)
        block = db.Column(db.String(50), nullable=True)
        village = db.Column(db.String(50), nullable=True)
        pin_code = db.Column(db.String(10), nullable=True)
        
        # Farming Information
        farm_size = db.Column(db.Float, nullable=True)  # in acres
        primary_crops = db.Column(db.Text, nullable=True)  # JSON string of crops
        farming_experience = db.Column(db.Integer, nullable=True)  # in years
        farm_type = db.Column(db.String(50), nullable=True)  # organic, conventional, mixed
        
        # Language Preference
        preferred_language = db.Column(db.String(5), default='ml', nullable=False)  # ml = Malayalam, en = English
        
        # Account Status
        is_active = db.Column(db.Boolean, default=True, nullable=False)
        is_verified = db.Column(db.Boolean, default=False, nullable=False)
        
        # Timestamps
        created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
        updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
        last_login = db.Column(db.DateTime, nullable=True)
        
        # Relationships - Define here to avoid deprecation warning
        queries = db.relationship('FarmerQuery', backref='farmer', lazy=True, cascade='all, delete-orphan')
        
        def __init__(self, username, phone, full_name, password):
            self.username = username
            self.phone = phone
            self.full_name = full_name
            self.set_password(password)
        
        def set_password(self, password):
            """Hash and set password"""
            self.password_hash = generate_password_hash(password)
        
        def check_password(self, password):
            """Check if provided password matches hash"""
            return check_password_hash(self.password_hash, password)
        
        def update_last_login(self):
            """Update last login timestamp"""
            self.last_login = datetime.utcnow()
        
        def get_profile_completion(self):
            """Calculate profile completion percentage"""
            total_fields = 12
            completed_fields = 0
            
            if self.email: completed_fields += 1
            if self.age: completed_fields += 1
            if self.gender: completed_fields += 1
            if self.district: completed_fields += 1
            if self.block: completed_fields += 1
            if self.village: completed_fields += 1
            if self.pin_code: completed_fields += 1
            if self.farm_size: completed_fields += 1
            if self.primary_crops: completed_fields += 1
            if self.farming_experience: completed_fields += 1
            if self.farm_type: completed_fields += 1
            completed_fields += 1  # Always count basic info as complete
            
            return round((completed_fields / total_fields) * 100)
        
        def to_dict(self):
            """Convert user object to dictionary"""
            return {
                'id': self.id,
                'username': self.username,
                'email': self.email,
                'phone': self.phone,
                'full_name': self.full_name,
                'age': self.age,
                'gender': self.gender,
                'district': self.district,
                'block': self.block,
                'village': self.village,
                'pin_code': self.pin_code,
                'farm_size': self.farm_size,
                'primary_crops': self.primary_crops,
                'farming_experience': self.farming_experience,
                'farm_type': self.farm_type,
                'preferred_language': self.preferred_language,
                'is_active': self.is_active,
                'is_verified': self.is_verified,
                'created_at': self.created_at.isoformat() if self.created_at else None,
                'updated_at': self.updated_at.isoformat() if self.updated_at else None,
                'last_login': self.last_login.isoformat() if self.last_login else None,
                'profile_completion': self.get_profile_completion()
            }
        
        def __repr__(self):
            return f'<User {self.username}>'
    
    return User