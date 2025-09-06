## Kerala Krishi AI - FastAPI + Flask Setup

Run backend services locally:

1) Create and activate virtualenv (optional if venv already present)
   - Windows PowerShell:
     - python -m venv venv
     - .\\venv\\Scripts\\Activate.ps1

2) Install dependencies
   - pip install -r requirements.txt

3) Start AI FastAPI service (port 5001)
   - set AI_SERVICE_PORT=5001
   - set GOOGLE_API_KEY=YOUR_KEY_HERE (optional for live Gemini)
   - python ai_service.py

4) Start Flask app (port 5000)
   - set FLASK_ENV=development
   - python app.py

The UI remains unchanged. The Flask app proxies AI features to the FastAPI service at http://localhost:5001.