"""模型引擎（厂商）查询、切换与在线接入接口。

权限模型（Key 按账号隔离）：
- GET  /api/providers        可选鉴权：登录后返回"你自己的"厂商状态，未登录返回部署方默认；
- POST /api/providers/switch 需登录：只改【当前账号】的偏好厂商，不再动全局状态；
- POST /api/providers/connect 需登录：Key 只写入【当前账号】，不影响其他账号、不写 .env。
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from .. import config
from ..providers import PROVIDERS
from .auth import current_user, optional_user

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
def get_providers(user: dict | None = Depends(optional_user)):
    return config.snapshot_for_user(user["id"] if user else None)


@router.post("/api/providers/switch")
def switch_provider(body: SwitchIn, user: dict = Depends(current_user)):
    try:
        return config.set_user_provider(user["id"], body.provider_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"未知厂商：{body.provider_id}")
    except PermissionError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/api/providers/connect")
def connect_provider(body: ConnectIn, user: dict = Depends(current_user)):
    if body.provider_id not in PROVIDERS:
        raise HTTPException(status_code=404, detail=f"未知厂商：{body.provider_id}")
    try:
        validate_key(body.provider_id, body.api_key)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    try:
        return config.register_user_key(user["id"], body.provider_id, body.api_key)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/api/providers/key/{provider_id}")
def delete_provider_key(provider_id: str, user: dict = Depends(current_user)):
    """移除当前账号在某厂商下的私有 Key（撤销误接入）。"""
    try:
        return config.remove_user_key(user["id"], provider_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"未知厂商：{provider_id}")
