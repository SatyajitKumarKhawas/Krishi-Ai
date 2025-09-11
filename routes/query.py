from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from datetime import datetime
import os
import json
import requests

query_bp = Blueprint('query', __name__)

@query_bp.route('/ask', methods=['GET', 'POST'])
@login_required
def ask_query():
    """Ask a new query page"""
    if request.method == 'POST':
        # Get models from app context - NO MORE FACTORY CALLS
        db = current_app.extensions['sqlalchemy']
        FarmerQuery = current_app.FarmerQuery
        QueryResponse = current_app.QueryResponse
        
        # Get form data
        query_text = request.form.get('query_text', '').strip()
        query_type = request.form.get('query_type', 'text')
        crop_type = request.form.get('crop_type', '').strip() or None
        urgency = request.form.get('urgency', 'medium')
        language = request.form.get('language', current_user.preferred_language)
        
        # Handle file uploads (only images are supported here)
        image_path = None
        audio_path = None
        image_file = None

        if 'image_file' in request.files:
            image_file = request.files['image_file']
            if image_file.filename != '' and current_app.allowed_file(image_file.filename):
                filename = secure_filename(image_file.filename)
                # Add timestamp to avoid filename conflicts
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
                filename = timestamp + filename
                image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                image_file.save(image_path)
                # Store relative path in database
                image_path = filename
        
        if 'audio_file' in request.files:
            audio_file = request.files['audio_file']
            if audio_file.filename != '' and current_app.allowed_file(audio_file.filename):
                # For now, we do not support audio in this flow
                flash('Only text OR image is supported right now (no audio).', 'error')
                return render_template('query/ask.html')

        # Enforce input exclusivity: either text OR image
        has_text = bool(query_text)
        has_image = bool(image_path)
        if has_text and has_image:
            flash('Please submit either text OR image, not both.', 'error')
            return render_template('query/ask.html')
        if not has_text and not has_image:
            flash('Please enter a question or upload an image.', 'error')
            return render_template('query/ask.html')
        
        try:
            # Create new query
            new_query = FarmerQuery(
                farmer_id=current_user.id,
                query_text=query_text,
                query_type=query_type,
                language=language
            )
            new_query.crop_type = crop_type
            new_query.urgency = urgency
            new_query.image_path = image_path
            new_query.audio_path = audio_path
            new_query.location = f"{current_user.village}, {current_user.district}" if current_user.village and current_user.district else None
            
            db.session.add(new_query)
            db.session.flush()  # Get the query ID

            # Call AI microservice
            ai_base = current_app.config.get('AI_SERVICE_URL', 'http://localhost:5001')

            if has_text:
                payload = {
                    'query_text': query_text,
                    'language': language,
                    'crop_type': crop_type,
                    'farmer_location': new_query.location,
                    'urgency': urgency,
                    'image_path': None,
                    'audio_path': None,
                    'farmer_context': {
                        'farm_size': getattr(current_user, 'farm_size', None),
                        'farming_experience': getattr(current_user, 'farming_experience', None),
                        'primary_crops': getattr(current_user, 'primary_crops', None),
                        'district': getattr(current_user, 'district', None)
                    }
                }
                try:
                    r = requests.post(f"{ai_base}/ai/answer", json=payload, timeout=30)
                    r.raise_for_status()
                    ai = r.json()
                    ai_text = ai.get('response_text') or 'No response generated.'
                    model_used = ai.get('model_used') or 'gemini-pro-2.0'
                    conf = ai.get('confidence_score') or None
                    ptime = ai.get('processing_time') or None
                    escalated = ai.get('escalated') or False
                except Exception as ex:
                    ai_text = 'AI service unavailable. Showing fallback advisory.' if language != 'ml' else 'AI സേവനം ലഭ്യമല്ല. താൽക്കാലിക നിർദ്ദേശം പ്രദർശിപ്പിക്കുന്നു.'
                    model_used = 'fallback'
                    conf = 0.3
                    ptime = 0.0
                    escalated = False
            else:
                # Image-only flow: send to Hugging Face via AI service
                try:
                    img_abs_path = os.path.join(current_app.config['UPLOAD_FOLDER'], image_path)
                    with open(img_abs_path, 'rb') as f:
                        files = {'image': (os.path.basename(img_abs_path), f, 'application/octet-stream')}
                        r = requests.post(f"{ai_base}/ai/process-image", files=files, timeout=60)
                    r.raise_for_status()
                    data = r.json()
                    if data.get('status') == 'success':
                        label = data.get('disease_detected') or 'Unknown'
                        score = data.get('confidence') or 0.0
                        ai_text = (
                            f"ചിത്ര വിശകലനം സൂചിപ്പിക്കുന്നത്: {label} (വിശ്വാസം {score:.2f})." if language == 'ml' 
                            else f"Image analysis suggests: {label} (confidence {score:.2f})."
                        )
                        model_used = 'huggingface'
                        conf = score
                        ptime = None
                        escalated = False
                    elif data.get('status') == 'loading':
                        ai_text = data.get('message') or (
                            'മോഡൽ ലോഡാകുന്നു, ദയവായി കുറച്ച് നേരം കഴിഞ്ഞ് വീണ്ടും ശ്രമിക്കുക.' if language == 'ml' 
                            else 'Model is loading, please retry shortly.'
                        )
                        model_used = 'huggingface'
                        conf = 0.0
                        ptime = None
                        escalated = False
                    else:
                        ai_text = data.get('message') or (
                            'ചിത്ര വിശകലനം ലഭ്യമല്ല.' if language == 'ml' else 'Image analysis unavailable.'
                        )
                        model_used = 'huggingface'
                        conf = 0.0
                        ptime = None
                        escalated = False
                except Exception as ex:
                    ai_text = 'AI image service unavailable. Showing fallback advisory.' if language != 'ml' else 'AI ചിത്രം സർവീസ് ലഭ്യമല്ല. താൽക്കാലിക നിർദ്ദേശം പ്രദർശിപ്പിക്കുന്നു.'
                    model_used = 'fallback'
                    conf = 0.3
                    ptime = 0.0
                    escalated = False

            ai_response = QueryResponse(
                query_id=new_query.id,
                response_text=ai_text,
                response_type='ai',
                language=language
            )
            ai_response.model_used = model_used
            ai_response.confidence_score = conf
            ai_response.processing_time = ptime

            db.session.add(ai_response)

            # Update query status and optionally escalate
            if escalated:
                new_query.status = 'escalated'
                try:
                    esc_payload = {
                        'query_text': query_text,
                        'metadata': {
                            'farmer_id': current_user.id,
                            'location': new_query.location,
                            'crop_type': crop_type,
                            'urgency': urgency
                        }
                    }
                    er = requests.post(f"{ai_base}/ai/escalate", json=esc_payload, timeout=10)
                    ticket = er.json().get('ticket_id') if er.ok else None
                    # Store escalation note
                    esc_note = QueryResponse(
                        query_id=new_query.id,
                        response_text=f"Escalated to local officer. Ticket: {ticket or 'pending'}",
                        response_type='escalated',
                        language=language
                    )
                    db.session.add(esc_note)
                except Exception:
                    pass
            else:
                new_query.status = 'answered'
            
            db.session.commit()
            
            flash('Your query has been submitted successfully!', 'success')
            return redirect(url_for('dashboard.view_query', query_id=new_query.id))
            
        except Exception as e:
            db.session.rollback()
            flash('Error submitting query. Please try again.', 'error')
            print(f"Query submission error: {e}")
    
    return render_template('query/ask.html')

@query_bp.route('/api/submit-query', methods=['POST'])
@login_required
def api_submit_query():
    """API endpoint to submit queries (for AJAX)"""
    db = current_app.extensions['sqlalchemy']
    FarmerQuery = current_app.FarmerQuery
    QueryResponse = current_app.QueryResponse
    
    try:
        data = request.get_json()
        
        # Create new query
        new_query = FarmerQuery(
            farmer_id=current_user.id,
            query_text=data.get('query_text'),
            query_type=data.get('query_type', 'text'),
            language=data.get('language', current_user.preferred_language)
        )
        new_query.crop_type = data.get('crop_type')
        new_query.urgency = data.get('urgency', 'medium')
        
        db.session.add(new_query)
        db.session.flush()
        
        # Call AI microservice
        ai_base = current_app.config.get('AI_SERVICE_URL', 'http://localhost:5001')
        payload = {
            'query_text': new_query.query_text,
            'language': new_query.language,
            'crop_type': new_query.crop_type,
            'farmer_location': new_query.location,
            'urgency': new_query.urgency
        }
        try:
            r = requests.post(f"{ai_base}/ai/answer", json=payload, timeout=20)
            r.raise_for_status()
            ai = r.json()
            ai_text = ai.get('response_text') or 'No response generated.'
            model_used = ai.get('model_used') or 'unknown'
            conf = ai.get('confidence_score') or None
            ptime = ai.get('processing_time') or None
            escalated = ai.get('escalated') or False
        except Exception:
            ai_text = 'AI service unavailable. Showing fallback advisory.'
            model_used = 'fallback'
            conf = 0.3
            ptime = 0.0
            escalated = False

        QueryResponse = current_app.QueryResponse
        ai_response = QueryResponse(
            query_id=new_query.id,
            response_text=ai_text,
            response_type='ai',
            language=new_query.language
        )
        ai_response.model_used = model_used
        ai_response.confidence_score = conf
        ai_response.processing_time = ptime
        current_app.extensions['sqlalchemy'].session.add(ai_response)

        if escalated:
            new_query.status = 'escalated'
            try:
                esc_payload = {
                    'query_text': new_query.query_text,
                    'metadata': {
                        'farmer_id': current_user.id,
                        'location': new_query.location,
                        'crop_type': new_query.crop_type,
                        'urgency': new_query.urgency
                    }
                }
                er = requests.post(f"{ai_base}/ai/escalate", json=esc_payload, timeout=10)
                ticket = er.json().get('ticket_id') if er.ok else None
                esc_note = QueryResponse(
                    query_id=new_query.id,
                    response_text=f"Escalated to local officer. Ticket: {ticket or 'pending'}",
                    response_type='escalated',
                    language=new_query.language
                )
                current_app.extensions['sqlalchemy'].session.add(esc_note)
            except Exception:
                pass
        else:
            new_query.status = 'answered'

        response = {
            'status': 'success',
            'query_id': new_query.id,
            'message': 'AI response generated',
            'escalated': escalated
        }
        
        db.session.commit()
        return jsonify(response)
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': 'Error submitting query'
        }), 500

@query_bp.route('/feedback/<int:response_id>', methods=['POST'])
@login_required
def submit_feedback(response_id):
    """Submit feedback for a response"""
    db = current_app.extensions['sqlalchemy']
    QueryResponse = current_app.QueryResponse
    FarmerQuery = current_app.FarmerQuery
    
    # Get the response and verify ownership
    response = db.session.query(QueryResponse).join(FarmerQuery).filter(
        QueryResponse.id == response_id,
        FarmerQuery.farmer_id == current_user.id
    ).first_or_404()
    
    # Get feedback data
    is_helpful = request.form.get('is_helpful') == 'yes'
    rating = int(request.form.get('rating', 0))
    feedback_text = request.form.get('feedback_text', '').strip() or None
    
    # Update response with feedback
    response.is_helpful = is_helpful
    response.rating = rating if 1 <= rating <= 5 else None
    response.feedback_text = feedback_text
    
    try:
        db.session.commit()
        flash('Thank you for your feedback!', 'success')
        
        # ===============================================
        # ML INTEGRATION POINT - FEEDBACK LEARNING
        # ===============================================
        # TODO: Send feedback to your ML system for learning
        # your_ml_service.record_feedback(
        #     response_id=response_id,
        #     is_helpful=is_helpful,
        #     rating=rating,
        #     feedback_text=feedback_text
        # )
        # ===============================================
        
    except Exception as e:
        db.session.rollback()
        flash('Error submitting feedback. Please try again.', 'error')
        print(f"Feedback error: {e}")
    
    return redirect(url_for('dashboard.view_query', query_id=response.query_id))

@query_bp.route('/process-image', methods=['POST'])
@login_required 
def process_image():
    """Process uploaded image for crop disease detection"""
    if 'image' not in request.files:
        return jsonify({'status': 'error', 'message': 'No image provided'}), 400
    image = request.files['image']
    ai_base = current_app.config.get('AI_SERVICE_URL', 'http://localhost:5001')
    files = {'image': (image.filename, image.stream, image.mimetype)}
    try:
        r = requests.post(f"{ai_base}/ai/process-image", files=files, timeout=30)
        r.raise_for_status()
        return jsonify(r.json())
    except Exception as e:
        return jsonify({'status': 'error', 'message': 'AI image service error'}), 500

@query_bp.route('/voice-to-text', methods=['POST'])
@login_required
def voice_to_text():
    """Convert voice input to text (Malayalam support)"""
    if 'audio' not in request.files:
        return jsonify({'status': 'error', 'message': 'No audio provided'}), 400
    audio = request.files['audio']
    language = request.form.get('language', 'ml')
    ai_base = current_app.config.get('AI_SERVICE_URL', 'http://localhost:5001')
    files = {'audio': (audio.filename, audio.stream, audio.mimetype)}
    data = {'language': language}
    try:
        r = requests.post(f"{ai_base}/ai/voice-to-text", files=files, data=data, timeout=60)
        r.raise_for_status()
        return jsonify(r.json())
    except Exception:
        return jsonify({'status': 'error', 'message': 'AI voice service error'}), 500