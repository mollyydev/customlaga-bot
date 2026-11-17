from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from fastapi import APIRouter, File, HTTPException, Request, UploadFile, status
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

from custom.services.customization_service import customization_service
from custom.services.emoji_service import emoji_service
from custom.services import language_service


CURRENT_DIR = Path(__file__).parent
TEMPLATES_DIR = CURRENT_DIR / "templates"
STATIC_DIR = CURRENT_DIR / "static"


class TranslateRequest(BaseModel):
    text: str
    source_lang: str = "ru"
    target_langs: list[str] | None = None


class EmojiPackRequest(BaseModel):
    url: str
    name: str | None = None


def create_customization_router() -> APIRouter:
    router = APIRouter(tags=["Customization"])

    @router.get("/customization", response_class=HTMLResponse)
    async def serve_customization_panel():
        panel_html = TEMPLATES_DIR / "panel.html"
        if not panel_html.exists():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Panel template not found")
        return HTMLResponse(content=panel_html.read_text(encoding="utf-8"))

    @router.get("/customization/static/{filename:path}")
    async def serve_static_file(filename: str):
        file_path = STATIC_DIR / filename
        if not file_path.exists():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Static file not found")
        content_type = "text/css" if filename.endswith(".css") else "application/javascript"
        return HTMLResponse(content=file_path.read_text(encoding="utf-8"), media_type=content_type)

    @router.get("/api/customization/config")
    async def get_config(request: Request):
        # Optional db session from request.state if available
        db = getattr(request.state, "db", None)
        config = await customization_service.get_config(db)
        return config.to_dict()

    @router.post("/api/customization/config")
    async def update_config(request: Request, patch_data: dict[str, Any]):
        db = getattr(request.state, "db", None)
        updated = await customization_service.update_config(db, patch_data)
        return updated.to_dict()

    @router.post("/api/customization/sync")
    async def sync_config_to_file():
        await customization_service.sync_to_disk()
        return {"status": "ok", "message": "Saved to JSON"}

    @router.post("/api/customization/translate")
    async def translate_endpoint(body: TranslateRequest):
        translations = await language_service.auto_translate_text(
            text=body.text,
            source_lang=body.source_lang,
            target_langs=body.target_langs,
        )
        return {"status": "ok", "translations": translations}

    @router.post("/api/customization/emoji-pack")
    async def add_emoji_pack_endpoint(body: EmojiPackRequest):
        pack = await emoji_service.add_emoji_pack(body.url, body.name)
        return pack

    @router.post("/api/customization/upload")
    async def upload_media_file(file: UploadFile = File(...)):
        from app.config import settings
        upload_dir = settings.get_media_upload_path()
        upload_dir.mkdir(parents=True, exist_ok=True)
        dest_path = upload_dir / file.filename
        content = await file.read()
        dest_path.write_bytes(content)
        return {"status": "ok", "file_url": f"/uploads/{file.filename}"}

    return router
