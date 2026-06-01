import os

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

MODEL_NAME = os.getenv("MODEL_NAME", "google/flan-t5-base")
MAX_NEW_TOKENS = int(os.getenv("MAX_NEW_TOKENS", "50"))
STATIC_DIR = "static"

app = FastAPI(title="FLAN-T5 API")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

tokenizer = None
model = None


class GenerateRequest(BaseModel):
    prompt: str


@app.on_event("startup")
def load_model() -> None:
    global tokenizer, model
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)


@app.get("/")
def home():
    return {
        "message": "API FLAN-T5 OK",
        "model_name": MODEL_NAME,
        "model_loaded": model is not None and tokenizer is not None,
    }


@app.get("/app")
def app_ui():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


@app.get("/health")
def health():
    return {
        "status": "ok",
        "model_loaded": model is not None and tokenizer is not None,
    }


@app.get("/generate")
def generate(prompt: str):
    if model is None or tokenizer is None:
        raise HTTPException(status_code=503, detail="Model not loaded yet")

    inputs = tokenizer(prompt, return_tensors="pt")
    outputs = model.generate(**inputs, max_new_tokens=MAX_NEW_TOKENS)
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return {"response": response}


@app.post("/generate")
def generate_post(payload: GenerateRequest):
    return generate(payload.prompt)
