"""模型引擎（厂商）查询、切换与在线接入接口。"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from .. import config
from ..providers import PROVIDERS

router = APIRouter()


class SwitchIn(BaseModel):
    provider_id: str


class ConnectIn(BaseModel):
    provider_id: str
    api_key: str


def validate_key(provider_id: str, api_key: str) -> None:
    """用一次最小对话调用验证 Key 可用性；失败抛 ValueError（含友好原因）。"""
    from openai import OpenAI

    p = PROVIDERS[provider_id]
    try:
        client = OpenAI(api_key=api_key.strip(), base_url=p["base_url"], timeout=20, max_retries=0)
        resp = client.chat.completions.create(
            model=p["text_model"],
            messages=[{"role": "user", "content": "请只回复两个字：收到"}],
            max_tokens=8,
            temperature=0,
        )
        if not (resp.choices[0].message.content or "").strip():
            raise ValueError("厂商返回了空响应，请稍后重试")
    except ValueError:
        raise
    except Exception as e:
        code = getattr(e, "status_code", None) or getattr(
            getattr(e, "response", None), "status_code", None
        )
        if code in (401, 403):
            raise ValueError("API Key 无效或没有权限，请检查后重新粘贴")
        if code == 429:
            raise ValueError("触发限流或账户欠费，请稍后重试或检查余额")
        msg = str(e)
        if "timed out" in msg or "timeout" in msg.lower():
            raise ValueError("连接厂商超时，请检查网络后重试")
        raise ValueError(f"连接失败：{msg[:120]}")


@router.get("/api/providers")
def get_providers():
    return config.snapshot()


@router.post("/api/providers/switch")
def switch_provider(body: SwitchIn):
    try:
        config.switch_provider(body.provider_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"未知厂商：{body.provider_id}")
    except PermissionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return config.snapshot()


@router.post("/api/providers/connect")
def connect_provider(body: ConnectIn):
    if body.provider_id not in PROVIDERS:
        raise HTTPException(status_code=404, detail=f"未知厂商：{body.provider_id}")
    try:
        validate_key(body.provider_id, body.api_key)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    try:
        config.register_key(body.provider_id, body.api_key)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return config.snapshot()
