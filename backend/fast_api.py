from typing import List
from io import BytesIO
from pathlib import Path
import os
import tempfile

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from docx import Document

from txt_agent import txt_agent
from UI_requirements import ui_schema_agent
from ui_preview_agent import ui_preview_agent

app = FastAPI(title="GigaProto API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def healthcheck() -> dict:
    return {"ok": True}


async def read_uploaded_file(file: UploadFile) -> str:
    filename = file.filename or "unknown"
    ext = Path(filename).suffix.lower()
    content = await file.read()

    if ext == ".txt":
        return content.decode("utf-8", errors="ignore")

    if ext == ".docx":
        doc = Document(BytesIO(content))
        return "\n".join(p.text for p in doc.paragraphs)

    if ext == ".doc":
        with tempfile.NamedTemporaryFile(delete=False, suffix=".doc") as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        try:
            import textract
            return textract.process(tmp_path).decode("utf-8", errors="ignore")
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    raise ValueError(f"Неподдерживаемый формат файла: {ext}")


@app.post("/generate")
async def generate(
    prompt: str = Form(""),
    files: List[UploadFile] = File(default=[]),
):
    parts: List[str] = []

    if prompt.strip():
        parts.append(f"Дополнительный комментарий пользователя:\n{prompt.strip()}")

    for file in files:
        file_text = await read_uploaded_file(file)
        parts.append(f"Содержимое файла {file.filename}:\n{file_text}")

    if not parts:
        return JSONResponse(
            status_code=400,
            content={"ok": False, "error": "Нет текста или файла для обработки"},
        )

    combined_text = "\n\n".join(parts)

    try:
        requirements_json = txt_agent(combined_text)
        ui_schema = ui_schema_agent(requirements_json)
        ui_preview = ui_preview_agent(ui_schema, requirements_json)

        return {
            "ok": True,
            "data": {
                "requirements": requirements_json,
                "ui_schema": ui_schema,
                "ui_preview": ui_preview,
            },
        }
    except Exception as exc:
        return JSONResponse(
            status_code=500,
            content={"ok": False, "error": f"Ошибка обработки файла: {str(exc)}"},
        )
