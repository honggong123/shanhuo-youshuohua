"""识图接口。

请求体兼容两种形式（见 files.read_image_and_form）：
- multipart/form-data：字段名 image（文件）  ← 小程序走这条，避开云托管文本请求 100KiB 限制
- application/json：{"image": "<base64>"}   ← 网页端沿用
"""
import base64
import time

from fastapi import APIRouter, Request
from fastapi.concurrency import run_in_threadpool

from .. import config
from ..files import MAX_IMAGE_BYTES, prune_dir, read_image_and_form
from ..schemas import RecognizeOut
from ..services import vision

router = APIRouter()

# 兼容旧引用
MAX_IMAGE_SIZE = MAX_IMAGE_BYTES


@router.post("/api/recognize", response_model=RecognizeOut)
async def recognize(request: Request):
    raw, _ = await read_image_and_form(request)
    # 毫秒时间戳避免同一秒内互相覆盖；滚动清理历史上传
    (config.UPLOADS_DIR / f"upload_{int(time.time() * 1000)}.jpg").write_bytes(raw)
    prune_dir(config.UPLOADS_DIR, keep=200)
    b64 = base64.b64encode(raw).decode()
    data = await run_in_threadpool(vision.recognize, b64)
    return RecognizeOut(**data)
