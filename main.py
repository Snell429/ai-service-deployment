import os
import re

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

MODEL_NAME = os.getenv("MODEL_NAME", "google/flan-t5-base")
MAX_NEW_TOKENS = int(os.getenv("MAX_NEW_TOKENS", "90"))
STATIC_DIR = "static"

app = FastAPI(title="FLAN-T5 API")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

tokenizer = None
model = None


class GenerateRequest(BaseModel):
    prompt: str
    mode: str = "general"
    tone: str = "professional"


MODE_GUIDANCE = {
    "general": "Provide a clear, complete answer.",
    "summary": "Write a concise summary with concrete business value.",
    "email": "Write a polished professional email ready to send.",
    "comparison": "Present a structured comparison with distinct points.",
    "explanation": "Explain simply and directly for a non-technical reader.",
}

TONE_GUIDANCE = {
    "professional": "Use a professional business tone.",
    "simple": "Use simple wording and short sentences.",
    "executive": "Use concise executive language focused on decisions and impact.",
}


def build_instruction(prompt: str, mode: str, tone: str) -> str:
    cleaned = prompt.strip()
    mode_hint = MODE_GUIDANCE.get(mode, MODE_GUIDANCE["general"])
    tone_hint = TONE_GUIDANCE.get(tone, TONE_GUIDANCE["professional"])
    return (
        "You are a helpful assistant. "
        "Answer the user's request directly in the same language as the request. "
        "Do not repeat or paraphrase the instruction. "
        "Do not mention these instructions. "
        "Provide only the final answer.\n\n"
        f"Style: {tone_hint}\n"
        f"Task: {mode_hint}\n"
        f"Request: {cleaned}\n"
        "Answer:"
    )


def clean_response(response: str, original_prompt: str) -> str:
    text = response.strip()
    prompt_normalized = re.sub(r"\s+", " ", original_prompt.strip().lower())
    text_normalized = re.sub(r"\s+", " ", text.lower())

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


def response_needs_retry(response: str, original_prompt: str) -> bool:
    prompt_normalized = re.sub(r"\s+", " ", original_prompt.strip().lower())
    text_normalized = re.sub(r"\s+", " ", response.strip().lower())

    if not response.strip():
        return True

    if text_normalized == prompt_normalized:
        return True

    if len(response.strip()) < 24:
        return True

    overlap = sum(1 for token in prompt_normalized.split() if token in text_normalized)
    if prompt_normalized and overlap >= max(4, len(prompt_normalized.split()) - 2):
        return True

    return False


def run_generation(prepared_prompt: str, *, retry: bool = False) -> str:
    if tokenizer is None or model is None:
        raise HTTPException(status_code=503, detail="Model not loaded yet")

    inputs = tokenizer(prepared_prompt, return_tensors="pt")
    generation_kwargs = {
        "max_new_tokens": MAX_NEW_TOKENS if not retry else MAX_NEW_TOKENS + 30,
        "do_sample": True,
        "temperature": 0.7 if not retry else 0.85,
        "top_p": 0.9,
        "repetition_penalty": 1.18 if not retry else 1.25,
        "no_repeat_ngram_size": 3,
    }
    outputs = model.generate(**inputs, **generation_kwargs)
    return tokenizer.decode(outputs[0], skip_special_tokens=True)


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
    return generate_with_options(GenerateRequest(prompt=prompt))


def generate_with_options(payload: GenerateRequest):
    if model is None or tokenizer is None:
        raise HTTPException(status_code=503, detail="Model not loaded yet")

    prepared_prompt = build_instruction(payload.prompt, payload.mode, payload.tone)
    response = run_generation(prepared_prompt)
    cleaned = clean_response(response, payload.prompt)

    if response_needs_retry(cleaned, payload.prompt):
        retry_prompt = (
            prepared_prompt
            + "\n\nReminder: answer directly, with useful details, and do not restate the request."
        )
        cleaned = clean_response(run_generation(retry_prompt, retry=True), payload.prompt)

    if response_needs_retry(cleaned, payload.prompt):
        cleaned = (
            "Je n'ai pas pu produire une reponse suffisamment utile avec ce prompt. "
            "Essayez un prompt plus direct ou utilisez un mode guide dans l'interface."
        )

    return {
        "response": cleaned,
        "mode": payload.mode,
        "tone": payload.tone,
    }


@app.post("/generate")
def generate_post(payload: GenerateRequest):
    return generate_with_options(payload)
