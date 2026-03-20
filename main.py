from fastapi import FastAPI, Path
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from schemas import GenerateRequest
from agents.orchestrator import orchestrate
from fastapi.staticfiles import StaticFiles
import os
import re

def split_llm_response_to_files(response_text, output_dir="generated"):
    os.makedirs(output_dir, exist_ok=True)

    # Регулярка ищет все блоки === filename.html === ...контент...
    pattern = r"===\s*(.+?\.html)\s*===\s*(.*?)(?=(?:===|$))"
    matches = re.findall(pattern, response_text, re.DOTALL)

    saved_files = []

    for filename, content in matches:
        filename = filename.strip()
        content = content.strip()

        # Сохраняем файл
        filepath = os.path.join(output_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        saved_files.append(filepath)

    return saved_files


app = FastAPI()
app.mount("/preview/generated", StaticFiles(directory="generated"), name="generated")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)
app.mount("/frontend", StaticFiles(directory="../frontend"), name="frontend")

@app.get("/", response_class=HTMLResponse)
async def home():
    with open("../frontend/index.html", "r", encoding="utf-8") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content)

@app.get("/preview/{page_name}", response_class=HTMLResponse)
async def preview(page_name: str = Path(...)):
    path = f"generated/{page_name}"
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        return HTMLResponse(content=content)
    except FileNotFoundError:
        return HTMLResponse(content=f"<h1>Страница {page_name} не найдена</h1>")
    

@app.post("/generate")
async def generate(request: GenerateRequest):
    prompt = request.prompt
    generated_site = await orchestrate(prompt)  # LLM выводит все страницы

    pages = split_llm_response_to_files(generated_site)
    print(pages)
    return JSONResponse({
        "pages": pages,
        "entry": pages[0] if pages else None  # первая страница для iframe
    })