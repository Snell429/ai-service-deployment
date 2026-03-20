from fastapi import FastAPI
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

app = FastAPI()

# Charger le modèle
tokenizer = AutoTokenizer.from_pretrained("google/flan-t5-base")
model = AutoModelForSeq2SeqLM.from_pretrained("google/flan-t5-base")

@app.get("/")
def home():
    return {"message": "API FLAN-T5 OK"}

@app.get("/generate")
def generate(prompt: str):
    inputs = tokenizer(prompt, return_tensors="pt")
    outputs = model.generate(**inputs, max_new_tokens=50)
    
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    
    return {"response": response}