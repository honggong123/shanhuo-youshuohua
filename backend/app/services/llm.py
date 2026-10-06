"""OpenAI 兼容接口的统一封装，未配置 key 时抛 LLMUnavailable，由路由层降级到演示数据。"""
import json
import re

from openai import OpenAI

from .. import config

TIMEOUT = 90


class LLMUnavailable(Exception):
    pass


def _client(api_key: str, base_url: str) -> OpenAI:
    if not api_key:
        raise LLMUnavailable("未配置 API Key")
    return OpenAI(api_key=api_key, base_url=base_url, timeout=TIMEOUT, max_retries=1)


def chat(messages: list[dict], *, model: str | None = None, api_key: str | None = None,
         base_url: str | None = None, temperature: float = 0.8) -> str:
    client = _client(api_key or config.LLM_API_KEY, base_url or config.LLM_BASE_URL)
    resp = client.chat.completions.create(
        model=model or config.LLM_MODEL, messages=messages, temperature=temperature,
    )
    return resp.choices[0].message.content or ""


def extract_json(text: str) -> dict:
    """从模型输出中提取第一个 JSON 对象（容忍 ```json 围栏）。"""
    text = re.sub(r"```(?:json)?", "", text).strip()
    start = text.find("{")
    if start == -1:
        raise ValueError("输出中未找到 JSON")
    depth = 0
    for i in range(start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return json.loads(text[start:i + 1])
    raise ValueError("JSON 未闭合")
