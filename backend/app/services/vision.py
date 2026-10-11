"""多模态识图：真实调用或演示数据。"""
import hashlib

from .. import config
from . import llm

VISION_PROMPT = (
    "你是农产品识别专家。请识别图片中的农产品/山货，只输出一个 JSON 对象，不要任何其他文字，"
    '格式：{"name":"产品名称","category":"品类(如新鲜水果/五谷杂粮/果干蜜饯/茶叶/天然滋补)",'
    '"origin":"国内最可能的产地(省市+县)","highlights":["外观或品质亮点",...最多4条],'
    '"description":"50字左右的介绍"}'
)


def _demo_result(image_b64: str) -> dict:
    idx = int(hashlib.md5(image_b64.encode()).hexdigest(), 16) % len(config_demo())
    return {**config_demo()[idx], "demo": True}


def config_demo():
    from ..demo_data import DEMO_PRODUCTS

    return DEMO_PRODUCTS


def recognize(image_b64: str, creds=None) -> dict:
    """识图。creds 为按账号解析出的凭据；不传则用部署方默认配置。

    按凭据链尝试（用户私有 → 部署方默认），全部失败才降级为演示数据。
    """
    if creds is None:
        creds = config.default_creds()
    data_url = f"data:image/jpeg;base64,{image_b64}"
    for c in config.creds_chain(creds):
        if not c.vision_key or not c.vision_model:
            continue
        try:
            text = llm.chat(
                [
                    {"role": "system", "content": "你是严谨的农产品识别助手，只输出 JSON。"},
                    {"role": "user", "content": [
                        {"type": "text", "text": VISION_PROMPT},
                        {"type": "image_url", "image_url": {"url": data_url}},
                    ]},
                ],
                model=c.vision_model,
                api_key=c.vision_key,
                base_url=c.vision_base,
                temperature=0.2,
            )
            data = llm.extract_json(text)
            data.setdefault("highlights", [])
            data["demo"] = False
            return data
        except Exception:
            continue  # 该凭据不可用 → 尝试链上的下一个
    # 全部失败时降级为演示数据，保证流程不中断
    return _demo_result(image_b64)
