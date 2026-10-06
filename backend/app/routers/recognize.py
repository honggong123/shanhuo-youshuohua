"""识图接口。"""
import base64
import time

from fastapi import APIRouter, HTTPException

from .. import config
from ..schemas import RecognizeIn, RecognizeOut
from ..services import vision

router = APIRouter()


def decode_image(image_str: str) -> bytes:
    s = image_str.strip()
    if "," in s and s.startswith("data:"):
        s = s.split(",", 1)[1]
    try:
        return base64.b64decode(s)
    except Exception:
        raise HTTPException(status_code=400, detail="图片 base64 解码失败")


@router.post("/api/recognize", response_model=RecognizeOut)
def recognize(body: RecognizeIn):
    raw = decode_image(body.image)
    (config.UPLOADS_DIR / f"upload_{int(time.time())}.jpg").write_bytes(raw)
    b64 = base64.b64encode(raw).decode()
    data = vision.recognize(b64)
    return RecognizeOut(**data)
