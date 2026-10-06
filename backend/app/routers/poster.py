"""文创海报生成接口。"""
from fastapi import APIRouter, HTTPException

from ..schemas import PosterIn, PosterOut
from ..services import poster

router = APIRouter()


@router.post("/api/poster", response_model=PosterOut)
def make_poster(body: PosterIn):
    try:
        path, ai = poster.compose(body.image, body.name.strip() or "山货",
                                  body.tagline.strip(), body.origin.strip())
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"海报生成失败：{e}")
    return PosterOut(url=f"/static/poster/{path.name}", ai_art=ai)
