from datetime import datetime

def create_farmer_query_model(db):
    """Factory function to create FarmerQuery model with db instance"""
    
    class FarmerQuery(db.Model):
        """Model to store farmer queries"""
        __tablename__ = 'farmer_queries'
        
        id = db.Column(db.Integer, primary_key=True)
        
        # Foreign Keys
        farmer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
        
        # Query Information
        query_text = db.Column(db.Text, nullable=False)
        query_type = db.Column(db.String(50), nullable=False)  # text, voice, image
        language = db.Column(db.String(5), default='ml', nullable=False)
        
        # Media Files (if any)
        image_path = db.Column(db.String(255), nullable=True)
        audio_path = db.Column(db.String(255), nullable=True)
        
        # Context Information
        crop_type = db.Column(db.String(50), nullable=True)
        season = db.Column(db.String(20), nullable=True)
        location = db.Column(db.String(100), nullable=True)
        urgency = db.Column(db.String(10), default='medium', nullable=False)  # low, medium, high, urgent
        
        # Query Status
        status = db.Column(db.String(20), default='pending', nullable=False)  # pending, processing, answered, escalated
        confidence_score = db.Column(db.Float, nullable=True)  # AI confidence in answer
        
        # Timestamps
        created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
        updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
        
        # Relationships - Define here to avoid deprecation warning
        responses = db.relationship('QueryResponse', backref='query', lazy=True, cascade='all, delete-orphan')
        
        def __init__(self, farmer_id, query_text, query_type='text', language='ml'):
            self.farmer_id = farmer_id
            self.query_text = query_text
            self.query_type = query_type
            self.language = language
        
        def to_dict(self):
            """Convert query object to dictionary"""
            return {
                'id': self.id,
                'farmer_id': self.farmer_id,
                'query_text': self.query_text,
                'query_type': self.query_type,
                'language': self.language,
                'image_path': self.image_path,
                'audio_path': self.audio_path,
                'crop_type': self.crop_type,
                'season': self.season,
                'location': self.location,
                'urgency': self.urgency,
                'status': self.status,
                'confidence_score': self.confidence_score,
                'created_at': self.created_at.isoformat() if self.created_at else None,
                'updated_at': self.updated_at.isoformat() if self.updated_at else None,
                'responses': [response.to_dict() for response in self.responses]
            }
        
        def __repr__(self):
            return f'<FarmerQuery {self.id}: {self.query_text[:50]}...>'
    
    return FarmerQuery