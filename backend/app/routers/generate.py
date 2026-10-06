"""文案 + 短视频脚本生成接口。"""
import hashlib

from fastapi import APIRouter

from .. import config
from ..price_reference import price_reference_for
from ..schemas import GenerateIn, GenerateOut, PriceInfo, Scene
from ..demo_data import DEMO_PRODUCTS
from ..services import llm

router = APIRouter()

PROMPT = """你是顶尖的农产品电商文案策划。请根据以下产品信息生成营销文案，只输出一个 JSON 对象，不要任何其他文字：
{{"title":"吸睛的主标题(12字内)","selling_points":["卖点1","卖点2","卖点3","卖点4"],
"story":"120字左右、有画面感的乡土故事","hashtags":["#话题1","#话题2","#话题3"],
"price":{{"reference":"市场参考价区间（必须严格依据下方行情锚点的数据，元/斤或元/件）","suggestion":"给农户的定价与包装建议（40字内，如礼盒化/分级定价策略）"}},
"value":["营养价值一句话","文化或产地价值一句话","送礼或食用场景一句话"],
"video_script":[{{"shot":"分镜1","visual":"画面描述","narration":"口播词"}},...]}}（3-5个分镜，口播词口语化，最后一个分镜引导购买）

行情锚点（价格依据，最高优先级，你给出的价格区间不得偏离）：
{price_block}

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
        price=PriceInfo(**p["price"]), value=p["value"], demo=True,
    )


def _parse_price(raw) -> PriceInfo:
    if isinstance(raw, dict):
        return PriceInfo(reference=str(raw.get("reference", "")), suggestion=str(raw.get("suggestion", "")))
    if raw:
        return PriceInfo(reference=str(raw))
    return PriceInfo()


@router.post("/api/generate", response_model=GenerateOut)
def generate(info: GenerateIn):
    if not config.LLM_API_KEY:
        return _demo(info)
    # 行情锚点：有核实行情则强制对齐，无则要求保守估算并注明
    ref = price_reference_for(info.name)
    if ref:
        price_block = f"以下行情已经人工核对，价格区间必须以此为锚：\n{ref}"
    else:
        price_block = "该产品暂无已核实行情，请按常识给出保守的价格区间，并在 reference 末尾注明“（估算参考）”。"
    try:
        text = llm.chat([
            {"role": "system", "content": "你是农产品营销文案专家，只输出 JSON。"},
            {"role": "user", "content": PROMPT.format(
                price_block=price_block,
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
            price=_parse_price(data.get("price")),
            value=[str(x) for x in data.get("value", [])][:4],
            video_script=[Scene(
                shot=str(s.get("shot", f"分镜{i+1}")),
                visual=str(s.get("visual", "")),
                narration=str(s.get("narration", "")),
            ) for i, s in enumerate(data.get("video_script", []))],
        )
    except Exception:
        return _demo(info)
