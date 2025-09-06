import os
from datetime import timedelta

class Config:
    # Basic Flask Configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Database Configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///farmer_support.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # File Upload Configuration
    UPLOAD_FOLDER = 'static/uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp3', 'wav', 'ogg'}
    
    # Session Configuration
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    
    # Malayalam Language Support
    LANGUAGES = {
        'en': 'English',
        'ml': 'Malayalam'
    }
    
    # AI Integration Endpoints (for future use)
    AI_SERVICE_URL = os.environ.get('AI_SERVICE_URL') or 'http://localhost:5001'
    ML_MODEL_PATH = os.environ.get('ML_MODEL_PATH') or 'models/crop_disease_model.pkl'

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_ECHO = True

class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'mysql://user:pass@localhost/farmer_support'

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}