"""文案 + 短视频脚本生成接口。"""
import hashlib

from fastapi import APIRouter

from .. import config
from ..schemas import GenerateIn, GenerateOut, Scene
from ..demo_data import DEMO_PRODUCTS
from ..services import llm

router = APIRouter()

PROMPT = """你是顶尖的农产品电商文案策划。请根据以下产品信息生成营销文案，只输出一个 JSON 对象，不要任何其他文字：
{{"title":"吸睛的主标题(12字内)","selling_points":["卖点1","卖点2","卖点3","卖点4"],
"story":"120字左右、有画面感的乡土故事","hashtags":["#话题1","#话题2","#话题3"],
"video_script":[{{"shot":"分镜1","visual":"画面描述","narration":"口播词"}},...]}}（3-5个分镜，口播词口语化，最后一个分镜引导购买）

产品信息：
- 名称：{name}
- 品类：{category}
- 产地：{origin}
- 亮点：{highlights}"""


def _demo(info: GenerateIn) -> GenerateOut:
    # 演示模式下优先按识别到的产品名精确匹配，保证识图与文案讲同一个产品
    p = next((x for x in DEMO_PRODUCTS if x["name"] == info.name.strip()), None)
    if p is None:
        idx = int(hashlib.md5(info.name.encode()).hexdigest(), 16) % len(DEMO_PRODUCTS)
        p = DEMO_PRODUCTS[idx]
    return GenerateOut(
        title=p["title"], selling_points=p["selling_points"], story=p["story"],
        hashtags=p["hashtags"], video_script=[Scene(**s) for s in p["video_script"]],
        demo=True,
    )


@router.post("/api/generate", response_model=GenerateOut)
def generate(info: GenerateIn):
    if not config.LLM_API_KEY:
        return _demo(info)
    try:
        text = llm.chat([
            {"role": "system", "content": "你是农产品营销文案专家，只输出 JSON。"},
            {"role": "user", "content": PROMPT.format(
                name=info.name, category=info.category or "农产品",
                origin=info.origin or "中国乡村", highlights="、".join(info.highlights) or "优质山货",
            )},
        ])
        data = llm.extract_json(text)
        return GenerateOut(
            title=str(data.get("title", info.name)).strip(),
            selling_points=[str(x) for x in data.get("selling_points", [])][:6],
            story=str(data.get("story", "")).strip(),
            hashtags=[str(x) for x in data.get("hashtags", [])][:5],
            video_script=[Scene(
                shot=str(s.get("shot", f"分镜{i+1}")),
                visual=str(s.get("visual", "")),
                narration=str(s.get("narration", "")),
            ) for i, s in enumerate(data.get("video_script", []))],
        )
    except Exception:
        return _demo(info)
