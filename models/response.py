from datetime import datetime

def create_query_response_model(db):
    """Factory function to create QueryResponse model with db instance"""
    
    class QueryResponse(db.Model):
        """Model to store responses to farmer queries"""
        __tablename__ = 'query_responses'
        
        id = db.Column(db.Integer, primary_key=True)
        
        # Foreign Keys
        query_id = db.Column(db.Integer, db.ForeignKey('farmer_queries.id'), nullable=False)
        
        # Response Information
        response_text = db.Column(db.Text, nullable=False)
        response_type = db.Column(db.String(20), default='ai', nullable=False)  # ai, human, escalated
        language = db.Column(db.String(5), default='ml', nullable=False)
        
        # AI Response Metadata
        model_used = db.Column(db.String(100), nullable=True)  # Which AI model generated the response
        confidence_score = db.Column(db.Float, nullable=True)
        processing_time = db.Column(db.Float, nullable=True)  # Time taken to generate response in seconds
        
        # Human Expert Information (if response_type = 'human')
        expert_name = db.Column(db.String(100), nullable=True)
        expert_designation = db.Column(db.String(100), nullable=True)
        expert_contact = db.Column(db.String(50), nullable=True)
        
        # Response Quality
        is_helpful = db.Column(db.Boolean, nullable=True)  # Farmer feedback
        rating = db.Column(db.Integer, nullable=True)  # 1-5 star rating
        feedback_text = db.Column(db.Text, nullable=True)  # Additional farmer feedback
        
        # Timestamps
        created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
        updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
        
        def __init__(self, query_id, response_text, response_type='ai', language='ml'):
            self.query_id = query_id
            self.response_text = response_text
            self.response_type = response_type
            self.language = language
        
        def to_dict(self):
            """Convert response object to dictionary"""
            return {
                'id': self.id,
                'query_id': self.query_id,
                'response_text': self.response_text,
                'response_type': self.response_type,
                'language': self.language,
                'model_used': self.model_used,
                'confidence_score': self.confidence_score,
                'processing_time': self.processing_time,
                'expert_name': self.expert_name,
                'expert_designation': self.expert_designation,
                'expert_contact': self.expert_contact,
                'is_helpful': self.is_helpful,
                'rating': self.rating,
                'feedback_text': self.feedback_text,
                'created_at': self.created_at.isoformat() if self.created_at else None,
                'updated_at': self.updated_at.isoformat() if self.updated_at else None
            }
        
        def __repr__(self):
            return f'<QueryResponse {self.id} for Query {self.query_id}>'
    
    return QueryResponse