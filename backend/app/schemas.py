"""接口数据模型。"""
from pydantic import BaseModel, Field


class RecognizeIn(BaseModel):
    image: str = Field(..., description="图片 base64 或 dataURL")


class RecognizeOut(BaseModel):
    name: str
    category: str
    origin: str
    highlights: list[str]
    description: str
    demo: bool = False


class GenerateIn(BaseModel):
    name: str
    category: str = ""
    origin: str = ""
    highlights: list[str] = []


class Scene(BaseModel):
    shot: str
    visual: str
    narration: str


class GenerateOut(BaseModel):
    title: str
    selling_points: list[str]
    story: str
    hashtags: list[str]
    video_script: list[Scene]
    demo: bool = False


class PosterIn(BaseModel):
    image: str = Field(..., description="产品照片 base64 或 dataURL")
    name: str
    tagline: str = ""
    origin: str = ""


class PosterOut(BaseModel):
    url: str
    ai_art: bool = False


class TtsIn(BaseModel):
    text: str
    voice: str = ""


class TtsOut(BaseModel):
    url: str
    voice: str


class Village(BaseModel):
    id: str
    name: str
    province: str
    tags: list[str]
    intro: str


class GuideIn(BaseModel):
    village_id: str
    question: str = ""


class GuideOut(BaseModel):
    village: str
    story: str
    audio_url: str | None = None
    demo: bool = False
