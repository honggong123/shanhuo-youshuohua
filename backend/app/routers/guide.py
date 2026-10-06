"""AI 数字讲解员接口：村落讲解 + 问答。"""
from fastapi import APIRouter, HTTPException

from .. import config
from ..services import llm
from ..villages import DEMO_VILLAGES, demo_story
from ..schemas import GuideIn, GuideOut, Village

router = APIRouter()

STORY_PROMPT = """你是乡村文旅数字讲解员。请以导游词口吻，为下面这个村庄写一段 300 字左右的沉浸式讲解，
要自然、有画面感、有感情，可以融入它的历史与产业特色，结尾欢迎游客到来。只输出讲解正文，不要标题和序号。

村庄：{name}（{province}）
背景：{intro}
特色标签：{tags}"""

QA_PROMPT = """你是乡村文旅数字讲解员，正在为游客讲解"{name}"（{province}）。背景资料：{intro}
请根据资料和你对乡村的了解，用 100 字以内、口语化的方式回答游客问题。

游客问题：{question}"""


def _find(village_id: str) -> dict:
    for v in DEMO_VILLAGES:
        if v["id"] == village_id:
            return v
    raise HTTPException(status_code=404, detail="未找到该村落")


@router.get("/api/villages", response_model=list[Village])
def villages():
    return [Village(**v) for v in DEMO_VILLAGES]


@router.post("/api/guide", response_model=GuideOut)
def guide(body: GuideIn):
    v = _find(body.village_id)
    demo = not config.LLM_API_KEY
    if body.question.strip():
        if demo:
            text = (f"（演示模式）关于{v['name']}：{v['intro']} "
                    f"这个问题非常好——简单说，{v['tags'][0]}是这里最大的特色。"
                    "配置大模型 API Key 后，我可以详细为你解答。")
        else:
            try:
                text = llm.chat([
                    {"role": "system", "content": "你是亲切的乡村文旅讲解员，回答简短口语化。"},
                    {"role": "user", "content": QA_PROMPT.format(
                        name=v["name"], province=v["province"], intro=v["intro"], question=body.question)},
                ], temperature=0.7)
            except Exception:
                text = f"关于{v['name']}：{v['intro']}"
    else:
        if demo:
            text = demo_story(v)
        else:
            try:
                text = llm.chat([
                    {"role": "system", "content": "你是专业的乡村文旅讲解员。"},
                    {"role": "user", "content": STORY_PROMPT.format(
                        name=v["name"], province=v["province"], intro=v["intro"],
                        tags="、".join(v["tags"]))},
                ], temperature=0.8)
            except Exception:
                text = demo_story(v)
    return GuideOut(village=v["name"], story=text.strip(), demo=demo)
