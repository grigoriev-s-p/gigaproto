from fastapi import FastAPI
from AI_client import ask_openrouter

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Hello World"}

@app.post("/generate")
def generate(prompt:str)->str:
    return ask_openrouter(prompt)