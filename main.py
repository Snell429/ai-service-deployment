import os
import re

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


def build_instruction(prompt: str) -> str:
    cleaned = prompt.strip()
    return (
        "You are a helpful assistant. "
        "Answer the user's request directly in the same language as the request. "
        "Do not repeat or paraphrase the instruction. "
        "Provide only the final answer.\n\n"
        f"Request: {cleaned}\n"
        "Answer:"
    )


def clean_response(response: str, original_prompt: str) -> str:
    text = response.strip()
    prompt_normalized = re.sub(r"\s+", " ", original_prompt.strip().lower())
    text_normalized = re.sub(r"\s+", " ", text.lower())

    if text_normalized == prompt_normalized:
        return "Je n'ai pas pu produire une reponse utile. Essayez un prompt plus direct ou plus encadre."

    prefixes = [
        "answer:",
        "reponse:",
        "response:",
        "instruction:",
        "question:",
        "request:",
    ]

    for prefix in prefixes:
        if text.lower().startswith(prefix):
            text = text[len(prefix):].strip()

    return text


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

    prepared_prompt = build_instruction(prompt)
    inputs = tokenizer(prepared_prompt, return_tensors="pt")
    outputs = model.generate(
        **inputs,
        max_new_tokens=MAX_NEW_TOKENS,
        do_sample=True,
        temperature=0.7,
        top_p=0.9,
        repetition_penalty=1.15,
        no_repeat_ngram_size=3,
    )
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return {"response": clean_response(response, prompt)}


@app.post("/generate")
def generate_post(payload: GenerateRequest):
    return generate(payload.prompt)
