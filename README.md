# 🌾 Krishi AI — Kerala Farmer Support System

Krishi AI is a bilingual (Malayalam / English) web platform that helps farmers in Kerala get quick, AI-powered answers to their farming questions — crop diseases, pest issues, weather-related concerns, and general agricultural advice — along with a dashboard to track past queries and manage their farmer profile.

The system is split into two services:
- A **Flask** web application that handles the UI, user accounts, farmer queries, and dashboard.
- A **FastAPI** microservice that handles AI-powered answer generation (via Google Gemini) and is called by the Flask app.

---

## ✨ Features

- **Farmer registration & login** with phone/email, profile details (district, block, village, farm size, crops grown, farming experience, etc.)
- **Ask a query** — submit questions as text, with optional image upload (e.g. a photo of a diseased crop)
- **AI-generated responses** — powered by Google Gemini, with confidence scoring and escalation for low-confidence answers
- **Query history dashboard** — view past queries and responses, leave feedback
- **Profile & settings management** — edit profile, change password, manage notification preferences
- **Malayalam and English language support**
- **Responsive UI** with custom styling and animations

---

## 🏗️ Project Structure

```
Krishi-Ai-main/
├── app.py                 # Flask application entry point
├── ai_service.py           # FastAPI AI microservice (Gemini integration)
├── config.py                # Flask app configuration (dev/prod)
├── requirements.txt
├── models/                  # SQLAlchemy models (User, FarmerQuery, QueryResponse)
├── routes/                  # Flask blueprints (auth, dashboard, query)
├── templates/                # Jinja2 HTML templates
├── static/                    # CSS, JS, uploaded files
└── instance/                   # SQLite database (farmer_support.db)
```

---

## ⚙️ Prerequisites

- Python 3.11 or 3.12
- pip
- (Optional) A [Google Gemini API key](https://ai.google.dev/) for live AI responses — without it, the AI service falls back to non-live behavior

---

## 🚀 Getting Started

### 1. Clone and set up a virtual environment

```bash
git clone <your-repo-url>
cd Krishi-Ai-main
python -m venv venv
```

Activate it:
- **Windows (PowerShell):** `.\venv\Scripts\Activate.ps1`
- **macOS/Linux:** `source venv/bin/activate`

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Create a `.env` file in the project root (do **not** commit this file):

```
GOOGLE_API_KEY=your_gemini_api_key_here
SECRET_KEY=your_flask_secret_key
AI_SERVICE_PORT=5001
AI_SERVICE_URL=http://localhost:5001
FLASK_ENV=development
```

> ⚠️ **Security note:** the `.env` file included in this project currently contains a real, exposed Google API key. Treat it as compromised — revoke/regenerate it in [Google AI Studio](https://aistudio.google.com/), remove it from `.env`, and make sure `.env` is listed in `.gitignore` so it's never committed to version control.

### 4. Start the AI microservice (FastAPI, port 5001)

```bash
python ai_service.py
```

### 5. Start the Flask web app (port 5000)

In a separate terminal (with the virtual environment activated):

```bash
python app.py
```

The Flask app automatically creates the SQLite database tables on first run.

### 6. Open the app

Visit **http://localhost:5000** in your browser.

---

## 🧩 How It Works

1. A logged-in farmer submits a query (text and/or image) via `/query/ask`.
2. The Flask app saves the query and forwards it to the FastAPI AI service at `AI_SERVICE_URL`.
3. The AI service builds a response using a lightweight retrieval step plus Google Gemini, returning the answer text, model used, and a confidence score.
4. The response is stored and displayed to the farmer, with an option to leave feedback.
5. Farmers can review all past queries and responses from their dashboard.

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Web framework | Flask, Flask-SQLAlchemy, Flask-Login, Flask-Migrate, Flask-WTF |
| AI microservice | FastAPI, Uvicorn |
| AI model | Google Gemini (`google-generativeai`) |
| Database | SQLite (dev) / MySQL (prod, via `PyMySQL`) |
| Auth | Werkzeug password hashing, Flask-Login sessions |
| Frontend | Jinja2 templates, custom CSS/JS |

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
