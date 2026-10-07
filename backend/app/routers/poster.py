"""文创海报生成接口。

请求体兼容 multipart/form-data（image 文件 + name/tagline/origin 文本字段）
与 application/json（image 为 base64），见 files.read_image_and_form。
"""
import base64

from fastapi import APIRouter, HTTPException, Request
from fastapi.concurrency import run_in_threadpool

from ..files import read_image_and_form
from ..schemas import PosterOut
from ..services import poster

router = APIRouter()


@router.post("/api/poster", response_model=PosterOut)
async def make_poster(request: Request):
    raw, fields = await read_image_and_form(request)
    name = (fields.get("name") or "").strip() or "山货"
    tagline = (fields.get("tagline") or "").strip()
    origin = (fields.get("origin") or "").strip()
    b64 = base64.b64encode(raw).decode()
    try:
        path, ai = await run_in_threadpool(poster.compose, b64, name, tagline, origin)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"海报生成失败：{e}")
    return PosterOut(url=f"/static/poster/{path.name}", ai_art=ai)
