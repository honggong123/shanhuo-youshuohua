"""生成文件的滚动清理 + 图片请求体的统一解析。"""
import base64
from pathlib import Path

from fastapi import HTTPException

# 单张图片上限（与云托管二进制请求 20MiB 额度对齐，留出余量）
MAX_IMAGE_BYTES = 15 * 1024 * 1024


def prune_dir(directory, keep: int = 200) -> None:
    d = Path(directory)
    if not d.exists():
        return
    files = sorted(d.glob("*"), key=lambda p: p.stat().st_mtime, reverse=True)
    for p in files[keep:]:
        try:
            p.unlink()
        except OSError:
            pass


def decode_base64_image(image_str: str) -> bytes:
    """解析 base64 或 dataURL 形式的图片。"""
    s = (image_str or "").strip()
    if not s:
        raise HTTPException(status_code=400, detail="缺少图片数据")
    if "," in s and s.startswith("data:"):
        s = s.split(",", 1)[1]
    try:
        raw = base64.b64decode(s)
    except Exception:
        raise HTTPException(status_code=400, detail="图片 base64 解码失败")
    if not raw:
        raise HTTPException(status_code=400, detail="图片内容为空")
    return raw


def _too_large() -> HTTPException:
    return HTTPException(
        status_code=400,
        detail=f"图片过大，请压缩后重试（≤{MAX_IMAGE_BYTES // 1024 // 1024}MB）",
    )


async def read_image_and_form(
    request, max_bytes: int = MAX_IMAGE_BYTES
) -> tuple[bytes, dict[str, str]]:
    """统一解析图片接口的请求体，兼容两种上传方式：

    1. ``multipart/form-data``（推荐）：``image`` 为文件字段，其余为普通文本字段。
       走二进制通道，不受云托管「文本请求 100KiB」限制（二进制额度 20MiB）。
    2. ``application/json``：``{"image": "<base64>"}``，兼容网页端与旧版小程序。

    返回 ``(图片原始字节, 文本字段字典)``。
    """
    ctype = (request.headers.get("content-type") or "").lower()

    if ctype.startswith("multipart/form-data"):
        form = await request.form()
        upload = form.get("image")
        if upload is None or isinstance(upload, str):
            raise HTTPException(status_code=400, detail="缺少图片文件字段 image")
        raw = await upload.read()
        if not raw:
            raise HTTPException(status_code=400, detail="图片内容为空")
        if len(raw) > max_bytes:
            raise _too_large()
        fields = {k: v for k, v in form.multi_items() if isinstance(v, str)}
        return raw, fields

    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="请求体需为 JSON 或 multipart/form-data")
    if not isinstance(body, dict):
        raise HTTPException(status_code=400, detail="请求体格式错误")

    raw = decode_base64_image(str(body.get("image", "")))
    if len(raw) > max_bytes:
        raise _too_large()
    fields = {
        k: str(v)
        for k, v in body.items()
        if k != "image" and isinstance(v, (str, int, float))
    }
    return raw, fields
