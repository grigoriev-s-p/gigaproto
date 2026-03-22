from typing import List
from io import BytesIO
from pathlib import Path
import json
import os
import tempfile

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from docx import Document

from txt_agent import txt_agent
from UI_requirements import ui_schema_agent
from ui_preview_agent import ui_preview_agent
from ui_edit_agent import apply_ui_edit
from recommendation_agent import build_recommendations
from recommendation_edit_bridge import resolve_edit_request

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
        recommendations = build_recommendations(requirements_json, ui_schema)

        return {
            "ok": True,
            "data": {
                "requirements": requirements_json,
                "ui_schema": ui_schema,
                "ui_preview": ui_preview,
                "recommendations": recommendations,
            },
        }
    except Exception as exc:
        return JSONResponse(
            status_code=500,
            content={"ok": False, "error": f"Ошибка обработки файла: {str(exc)}"},
        )


@app.post("/edit")
async def edit(
    current_requirements: str = Form(...),
    current_ui_schema: str = Form(...),
    current_ui_preview: str = Form(...),
    user_edit: str = Form(...),
    pending_recommendations: str = Form("[]"),
):
    try:
        current_requirements_dict = json.loads(current_requirements)
        current_ui_schema_dict = json.loads(current_ui_schema)
        current_preview_dict = json.loads(current_ui_preview)

        parsed_pending = json.loads(pending_recommendations) if pending_recommendations else []
        pending_recommendations_list = parsed_pending if isinstance(parsed_pending, list) else []

        edit_plan = resolve_edit_request(user_edit, pending_recommendations_list)

        if edit_plan["mode"] == "decline":
            return {
                "ok": True,
                "data": {
                    "requirements": current_requirements_dict,
                    "ui_schema": current_ui_schema_dict,
                    "ui_preview": current_preview_dict,
                    "recommendations": [],
                    "summary": edit_plan.get("summary") or "Понял, рекомендации не применяю.",
                    "applied_recommendations": False,
                    "dismissed_recommendations": True,
                },
            }

        result = apply_ui_edit(
            edit_request=edit_plan["edit_request"],
            current_requirements=current_requirements_dict,
            current_ui_schema=current_ui_schema_dict,
            current_ui_preview=current_preview_dict,
        )

        refreshed_recommendations = build_recommendations(result["requirements"], result["ui_schema"])

        return {
            "ok": True,
            "data": {
                "requirements": result["requirements"],
                "ui_schema": result["ui_schema"],
                "ui_preview": result["ui_preview"],
                "recommendations": refreshed_recommendations,
                "summary": result["summary"],
                "applied_recommendations": bool(edit_plan.get("applied_recommendations")),
                "dismissed_recommendations": bool(edit_plan.get("dismissed_recommendations")),
            },
        }
    except Exception as exc:
        return JSONResponse(
            status_code=500,
            content={"ok": False, "error": f"Ошибка правки: {str(exc)}"},
        )
