from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from AI_client import ask_openrouter
from pydantic import BaseModel

class Request(BaseModel):
    prompt: str
    
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # для разработки нормально
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "Hello World"}

@app.post("/generate")
def generate(data: Request):
    answer = ask_openrouter(data.prompt)
    return {"answer": answer}



