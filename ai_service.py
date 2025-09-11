import os
import time
import math
from typing import List, Optional, Dict, Any

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from pathlib import Path
from dotenv import dotenv_values

try:
    import google.generativeai as genai
except Exception:
    genai = None


class Document(BaseModel):
    id: str
    text: str
    metadata: Dict[str, Any] = {}


class AnswerRequest(BaseModel):
    query_text: str
    language: str = "ml"
    crop_type: Optional[str] = None
    farmer_location: Optional[str] = None
    urgency: Optional[str] = None
    image_path: Optional[str] = None
    audio_path: Optional[str] = None
    farmer_context: Optional[Dict[str, Any]] = None
    history: Optional[List[Dict[str, Any]]] = None


class AnswerResponse(BaseModel):
    response_text: str
    model_used: str
    confidence_score: float
    processing_time: float
    escalated: bool = False


def cosine_similarity(a: List[float], b: List[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


class InMemoryRetriever:
    def __init__(self, docs: List[Document]):
        self.docs = docs
        self.vocab: Dict[str, int] = {}
        self.doc_vectors: List[List[float]] = []
        self._build_index()

    def _tokenize(self, text: str) -> List[str]:
        return [t.lower() for t in text.split()]

    def _vectorize(self, text: str) -> List[float]:
        vec = [0.0] * len(self.vocab)
        for token in self._tokenize(text):
            if token not in self.vocab:
                continue
            vec[self.vocab[token]] += 1.0
        return vec

    def _build_index(self) -> None:
        # build vocab
        idx = 0
        for d in self.docs:
            for token in self._tokenize(d.text):
                if token not in self.vocab:
                    self.vocab[token] = idx
                    idx += 1
        # precompute doc vectors
        self.doc_vectors = [self._vectorize(d.text) for d in self.docs]

    def query(self, text: str, top_k: int = 3) -> List[Document]:
        qv = self._vectorize(text)
        scored = []
        for i, dv in enumerate(self.doc_vectors):
            score = cosine_similarity(qv, dv)
            scored.append((score, i))
        scored.sort(reverse=True)
        results: List[Document] = []
        for score, i in scored[:top_k]:
            d = self.docs[i]
            d.metadata = {**d.metadata, "similarity": float(score)}
            results.append(d)
        return results


def load_seed_knowledge() -> List[Document]:
    # Minimal seed; in a real app load from files/DB
    seeds = [
        ("pest_banana_leaf_spot", "For banana leaf spot (Sigatoka), use mancozeb or propiconazole as per label. Ensure proper sanitation and remove affected leaves.", {"crop": "Banana", "topic": "pest"}),
        ("rice_blast", "Rice blast can be managed with tricyclazole; avoid excess nitrogen and maintain field hygiene.", {"crop": "Rice", "topic": "disease"}),
        ("kerala_weather", "Check IMD Kerala district forecast; heavy rain June-Sep. Ensure drainage in low-lying fields.", {"topic": "weather"}),
        ("schemes_subsidy", "For subsidies, refer to Kerala Department of Agriculture e-Krishi portal and PM-KISAN eligibility.", {"topic": "scheme"}),
    ]
    return [Document(id=i, text=t, metadata=m) for i, t, m in seeds]


def build_prompt(req: AnswerRequest, contexts: List[Document]) -> str:
    sys_msg = (
        "You are Kerala Krishi AI, a helpful, reliable agricultural advisor. "
        "Be concise, step-wise, and safe."
    )
    ctx = "\n\n".join([f"[Context {i+1}] {d.text}" for i, d in enumerate(contexts)])
    user_ctx = []
    if req.crop_type:
        user_ctx.append(f"Crop: {req.crop_type}")
    if req.farmer_location:
        user_ctx.append(f"Location: {req.farmer_location}")
    if req.urgency:
        user_ctx.append(f"Urgency: {req.urgency}")
    if req.image_path:
        user_ctx.append(f"Image provided: {req.image_path}")
    if req.audio_path:
        user_ctx.append(f"Audio provided: {req.audio_path}")
    user_ctx_str = " | ".join(user_ctx)
    lang_rule = (
        "RESPONSE LANGUAGE: Respond STRICTLY in Malayalam. Do NOT use English words except crop/chemical names if unavoidable."
        if req.language == "ml" else
        "RESPONSE LANGUAGE: Respond in English."
    )
    return (
        f"{sys_msg}\n{lang_rule}\n\nKnowledge:\n{ctx}\n\n"
        f"UserContext: {user_ctx_str}\n\n"
        f"Question: {req.query_text}\n\n"
        "Provide clearly labeled sections: 1) Direct Answer, 2) Steps, 3) Safety, 4) Unclear Information."
    )


def call_gemini(prompt: str, language: str) -> str:
    api_key = os.environ.get("GOOGLE_API_KEY")
    if genai is None or not api_key:
        if language == "ml":
            return (
                "ഇപ്പോൾ ഡീഫോൾട്ട് മറുപടി നൽകുന്നു. കൂടുതൽ കൃത്യമായ മറുപടി ലഭിക്കാൻ AI കീ ചേർക്കുക.\n"
                "1) പൊതു നിർദ്ദേശം: വിള പരിപാലനം മെച്ചപ്പെടുത്തുക.\n2) സുരക്ഷ: ലേബൽപ്രകാരം മാത്രം കീടനാശിനി ഉപയോഗിക്കുക."
            )
        return (
            "Default advisory. Add GOOGLE_API_KEY for live AI.\n"
            "1) Improve crop management.\n2) Safety: Follow label directions strictly."
        )
    try:
        genai.configure(api_key=api_key)
        for model_name in ["gemini-1.5-flash"]:
            try:
                model = genai.GenerativeModel(model_name)
                resp = model.generate_content(prompt)
                if getattr(resp, 'text', None):
                    return resp.text
            except Exception:
                continue
    except Exception:
        pass
    if language == "ml":
        return (
            "ഇപ്പോൾ ഡീഫോൾട്ട് മറുപടി നൽകുന്നു. കൂടുതൽ കൃത്യമായ മറുപടി ലഭിക്കാൻ AI കീ ചേർക്കുക.\n"
            "1) പൊതു നിർദ്ദേശം: വിള പരിപാലനം മെച്ചപ്പെടുത്തുക.\n2) സുരക്ഷ: ലേബൽപ്രകാരം മാത്രം കീടനാശിനി ഉപയോഗിക്കുക."
        )
    return (
        "Default advisory. Add GOOGLE_API_KEY for live AI.\n"
        "1) Improve crop management.\n2) Safety: Follow label directions strictly."
    )


# Ensure .env in the same directory is loaded reliably (even across cwd changes)
_env_path = Path(__file__).with_name('.env')
load_dotenv(dotenv_path=str(_env_path), override=True)
try:
    # Force load .env into os.environ if any key missing
    values = dotenv_values(str(_env_path))
    for _k, _v in values.items():
        if _v is not None and (os.environ.get(_k) in (None, '')):
            os.environ[_k] = _v
except Exception:
    pass

app = FastAPI(title="Kerala Krishi AI Service")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

retriever = InMemoryRetriever(load_seed_knowledge())


@app.get("/ai/debug")
def ai_debug():
    api_key = os.environ.get("GOOGLE_API_KEY")
    hf_key = os.environ.get("HF_API_TOKEN")
    return {
        "genai_imported": genai is not None,
        "google_key_present": bool(api_key),
        "google_key_prefix": (api_key[:6] + "...") if api_key else None,
        "hf_key_present": bool(hf_key),
        "hf_key_prefix": (hf_key[:6] + "...") if hf_key else None,
    }

@app.post("/ai/answer", response_model=AnswerResponse)
def ai_answer(req: AnswerRequest):
    start = time.time()
    contexts = retriever.query(req.query_text, top_k=3)
    prompt = build_prompt(req, contexts)
    answer = call_gemini(prompt, req.language)
    # naive confidence from top similarity
    top_sim = float(contexts[0].metadata.get("similarity", 0.4)) if contexts else 0.4
    escalated = top_sim < 0.15
    return AnswerResponse(
        response_text=answer,
        model_used="gemini-pro-2.0",
        confidence_score=max(0.3, min(0.95, top_sim + 0.3)),
        processing_time=round(time.time() - start, 3),
        escalated=escalated,
    )


@app.post("/ai/voice-to-text")
async def ai_voice_to_text(
    audio: UploadFile = File(...),
    language: str = Form("ml"),
):
    # Stub: In production, call STT service
    filename = audio.filename
    text_ml = "ഓഡിയോ ട്രാൻസ്ക്രിപ്ഷൻ സജ്ജമല്ല. താൽക്കാലിക മറുപടി."  # temporary
    text_en = "Voice transcription service not configured. Returning placeholder."
    return {
        "status": "success",
        "text": text_ml if language == "ml" else text_en,
        "language": language,
        "filename": filename,
        "confidence": 0.5,
    }


@app.post("/ai/process-image")
async def ai_process_image(image: UploadFile = File(...)):
    # Use Hugging Face Inference API for image classification
    # Configure via env:
    #   HF_API_TOKEN: personal access token
    #   HF_IMAGE_MODEL: model repo id (default: microsoft/resnet-50)
    try:
        contents = await image.read()
    except Exception:
        raise HTTPException(status_code=400, detail="Unable to read image upload")

    hf_token = os.environ.get("HF_API_TOKEN")
    model_id = os.environ.get("HF_IMAGE_MODEL", "microsoft/resnet-50")

    if not contents:
        raise HTTPException(status_code=400, detail="Empty image content")

    if not hf_token:
        # Fallback response when token not provided
        return {
            "status": "success",
            "disease_detected": None,
            "confidence": 0.0,
            "treatment_suggestions": [],
            "message": "Hugging Face token not configured. Set HF_API_TOKEN to enable image analysis.",
        }

    try:
        import requests  # already in requirements

        headers = {
            "Authorization": f"Bearer {hf_token}",
        }
        resp = requests.post(
            f"https://api-inference.huggingface.co/models/{model_id}",
            headers=headers,
            data=contents,
            timeout=60,
        )
        if resp.status_code == 503:
            # Model loading; return informative message
            data = resp.json()
            return {
                "status": "loading",
                "message": data.get("error", "Model loading"),
            }
        resp.raise_for_status()
        data = resp.json()
        # Response formats can vary; handle common classification schema
        top_label = None
        top_score = None
        if isinstance(data, list) and data and isinstance(data[0], list):
            # Some endpoints return list[list[{label, score}, ...]]
            preds = data[0]
        else:
            preds = data
        if isinstance(preds, list) and preds:
            best = max(preds, key=lambda x: x.get("score", 0))
            top_label = best.get("label")
            top_score = float(best.get("score", 0.0))

        return {
            "status": "success",
            "disease_detected": top_label,
            "confidence": top_score if top_score is not None else 0.0,
            "treatment_suggestions": [],
            "message": "",
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Image analysis failed: {e}",
        }


class FeedbackRequest(BaseModel):
    response_id: Optional[int] = None
    is_helpful: Optional[bool] = None
    rating: Optional[int] = None
    feedback_text: Optional[str] = None


@app.post("/ai/feedback")
def ai_feedback(req: FeedbackRequest):
    # No persistent store; pretend to learn
    return {"status": "ok"}


class EscalationRequest(BaseModel):
    query_text: str
    metadata: Dict[str, Any] = {}


@app.post("/ai/escalate")
def ai_escalate(req: EscalationRequest):
    # In production, notify officer via email/SMS
    ticket_id = f"ESC-{int(time.time())}"
    return {"status": "queued", "ticket_id": ticket_id}


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("AI_SERVICE_PORT", "5001"))
    uvicorn.run("ai_service:app", host="0.0.0.0", port=port, reload=True)


