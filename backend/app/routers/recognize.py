"""识图接口。"""
import base64
import time

from fastapi import APIRouter, HTTPException

from .. import config
from ..files import prune_dir
from ..schemas import RecognizeIn, RecognizeOut
from ..services import vision

router = APIRouter()

MAX_IMAGE_SIZE = 15 * 1024 * 1024  # 15MB


def decode_image(image_str: str) -> bytes:
    s = image_str.strip()
    if "," in s and s.startswith("data:"):
        s = s.split(",", 1)[1]
    try:
        raw = base64.b64decode(s)
    except Exception:
        raise HTTPException(status_code=400, detail="图片 base64 解码失败")
    if len(raw) > MAX_IMAGE_SIZE:
        raise HTTPException(status_code=400, detail="图片过大，请压缩后重试（≤15MB）")
    return raw


@router.post("/api/recognize", response_model=RecognizeOut)
def recognize(body: RecognizeIn):
    raw = decode_image(body.image)
    # 毫秒时间戳避免同一秒内互相覆盖；滚动清理历史上传
    (config.UPLOADS_DIR / f"upload_{int(time.time() * 1000)}.jpg").write_bytes(raw)
    prune_dir(config.UPLOADS_DIR, keep=200)
    b64 = base64.b64encode(raw).decode()
    data = vision.recognize(b64)
    return RecognizeOut(**data)
