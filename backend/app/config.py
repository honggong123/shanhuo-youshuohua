"""读取 .env 配置；支持多厂商 Key 与运行时动态切换。

- 各厂商 Key 在 .env 中按 providers.py 约定的环境变量名配置；
- 兼容旧配置：单一 LLM_API_KEY 视为智谱 GLM 的 Key；
- DEFAULT_PROVIDER 指定默认厂商（auto = 第一个有 Key 的厂商）；
- 未配置任何 Key 时自动进入演示模式（DEMO_MODE = True）。
"""
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

from .providers import PROVIDERS

BACKEND_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BACKEND_DIR / ".env")

GENERATED_DIR = BACKEND_DIR / "generated"
UPLOADS_DIR = BACKEND_DIR / "uploads"
(GENERATED_DIR / "poster").mkdir(parents=True, exist_ok=True)
(GENERATED_DIR / "audio").mkdir(parents=True, exist_ok=True)
UPLOADS_DIR.mkdir(exist_ok=True)


def _find_frontend_dist() -> Path:
    """定位网页版构建产物。

    两种部署形态的目录关系不同，必须都支持：
    - 本地 / 云服务器（仓库根构建）：backend/app/ ← BACKEND_DIR=backend/，
      产物在 仓库根/frontend/dist   → BACKEND_DIR.parent/frontend/dist
    - 容器（上传包构建）：/srv/app/ ← BACKEND_DIR=/srv，
      产物在 /srv/frontend/dist     → BACKEND_DIR/frontend/dist
    优先取「与 app 同级」的位置，再回退到「上一级」的旧约定。
    """
    candidates = [
        BACKEND_DIR / "frontend" / "dist",
        BACKEND_DIR.parent / "frontend" / "dist",
    ]
    for c in candidates:
        if (c / "index.html").exists():
            return c
    return candidates[-1]  # 都不存在时返回旧约定路径，main.py 会跳过挂载


FRONTEND_DIST = _find_frontend_dist()


def _env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


# ---- 收集各厂商 Key（兼容旧 LLM_API_KEY → glm）----
KEYS: dict[str, str] = {}
for _pid, _p in PROVIDERS.items():
    _k = _env(_p["key_env"])
    if _k:
        KEYS[_pid] = _k
if "glm" not in KEYS:
    _legacy = _env("LLM_API_KEY")
    if _legacy:
        KEYS["glm"] = _legacy

# 默认厂商：DEFAULT_PROVIDER 指定；auto 或无效时取第一个有 Key 的
_requested = _env("DEFAULT_PROVIDER", "auto").lower()
if _requested == "auto":
    _default_pid = next(iter(KEYS), None)
elif _requested in PROVIDERS and _requested in KEYS:
    _default_pid = _requested
else:
    _default_pid = None

# 服务配置
TTS_VOICE = _env("TTS_VOICE", "zh-CN-XiaoxiaoNeural")
HOST = _env("HOST", "127.0.0.1")
PORT = int(_env("PORT", "8000"))

# ---- 当前生效的厂商与模型（由 _apply 维护，可运行时切换）----
ACTIVE_PROVIDER: str | None = None
DEMO_MODE = True
LLM_API_KEY = ""
LLM_BASE_URL = ""
LLM_MODEL = ""
VISION_API_KEY = ""
VISION_BASE_URL = ""
VISION_MODEL = ""  # 空串表示该厂商不支持识图
IMG_API_KEY = ""
IMG_BASE_URL = ""
IMG_MODEL = ""  # 空串表示该厂商不支持生图
IMG_SIZE = ""  # 生图尺寸（各厂商支持的档位不同）


def _apply(pid: str | None) -> None:
    """把厂商 pid 的连接信息应用到当前配置；pid 为 None 时进入演示模式。"""
    global ACTIVE_PROVIDER, DEMO_MODE
    global LLM_API_KEY, LLM_BASE_URL, LLM_MODEL
    global VISION_API_KEY, VISION_BASE_URL, VISION_MODEL
    global IMG_API_KEY, IMG_BASE_URL, IMG_MODEL, IMG_SIZE

    if pid is None or pid not in KEYS:
        ACTIVE_PROVIDER = None
        DEMO_MODE = True
        LLM_API_KEY = LLM_BASE_URL = LLM_MODEL = ""
        VISION_API_KEY = VISION_BASE_URL = VISION_MODEL = ""
        IMG_API_KEY = IMG_BASE_URL = IMG_MODEL = IMG_SIZE = ""
        return

    p = PROVIDERS[pid]
    ACTIVE_PROVIDER = pid
    DEMO_MODE = False
    LLM_API_KEY = KEYS[pid]
    LLM_BASE_URL = p["base_url"]
    LLM_MODEL = p["text_model"]
    VISION_API_KEY = KEYS[pid]
    VISION_BASE_URL = p["base_url"]
    VISION_MODEL = p["vision_model"] or ""
    IMG_API_KEY = KEYS[pid]
    IMG_BASE_URL = p["base_url"]
    IMG_MODEL = p["img_model"] or ""
    IMG_SIZE = p.get("img_size") or ""


_apply(_default_pid)


@dataclass(frozen=True)
class Creds:
    """一次请求实际使用的大模型连接信息（已按账号解析完毕）。"""

    provider: str | None = None
    demo: bool = True
    llm_key: str = ""
    llm_base: str = ""
    llm_model: str = ""
    vision_key: str = ""
    vision_base: str = ""
    vision_model: str = ""
    img_key: str = ""
    img_base: str = ""
    img_model: str = ""
    img_size: str = ""


def _capability(ukeys: dict[str, str], need: str) -> tuple[str, str]:
    """为某项能力（vision_model / img_model）挑一个"支持它"的厂商。

    优先用户私有 Key，其次部署方默认 Key；都没有则返回 ("", "")。
    """
    for pid, k in ukeys.items():
        if PROVIDERS[pid].get(need):
            return pid, k
    for pid in KEYS:
        if PROVIDERS[pid].get(need):
            return pid, KEYS[pid]
    return "", ""


def creds_for_user(user_id: int | None) -> Creds:
    """按账号解析凭据。

    - 文本能力：用户偏好厂商 → 用户第一个私有 Key → 部署方默认；
    - 识图 / 生图：所选厂商支持就用它；**不支持时自动回退**到"支持该能力"的
      厂商（先用户私有、再部署方），避免用户接入一个纯文本 Key 后识图/海报
      退化成演示数据；
    - 完全无可用 Key → 演示模式。

    未登录（user_id 为 None）时等价于只用部署方默认 Key，保证免登录也能演示。
    """
    ukeys: dict[str, str] = {}
    pref = ""
    if user_id:
        from . import db  # 延迟导入，避免与 db.py 形成循环依赖

        ukeys = db.user_keys(user_id)
        pref = db.user_active_provider(user_id)

    # ---- 文本厂商 ----
    text_pid = None
    if pref and (pref in ukeys or pref in KEYS):
        text_pid = pref
    elif ukeys:
        text_pid = next(iter(ukeys))
    elif ACTIVE_PROVIDER:
        text_pid = ACTIVE_PROVIDER
    if not text_pid:
        return Creds()  # provider=None → 演示模式
    text_key = ukeys.get(text_pid) or KEYS.get(text_pid)
    if not text_key:
        return Creds()
    tp = PROVIDERS[text_pid]

    # ---- 识图 / 生图（支持则沿用所选厂商，否则回退）----
    def cap(need: str) -> tuple[str, str, str, str]:
        if tp.get(need):
            return text_pid, text_key, tp["base_url"], tp[need]
        pid, k = _capability(ukeys, need)
        if not pid:
            return "", "", "", ""
        p = PROVIDERS[pid]
        return pid, k, p["base_url"], p[need]

    _, vk, vb, vm = cap("vision_model")
    ipid, ik, ib, im = cap("img_model")

    return Creds(
        provider=text_pid,
        demo=False,
        llm_key=text_key,
        llm_base=tp["base_url"],
        llm_model=tp["text_model"],
        vision_key=vk,
        vision_base=vb,
        vision_model=vm,
        img_key=ik,
        img_base=ib,
        img_model=im,
        img_size=(PROVIDERS[ipid].get("img_size") or "") if ipid else "",
    )


def default_creds() -> Creds:
    """部署方默认凭据（未登录用户、或未配置私有 Key 的用户使用）。"""
    return creds_for_user(None)


def fallback_creds(creds: Creds) -> Creds | None:
    """用户私有凭据不可用时的兜底（部署方默认）；无需兜底时返回 None。

    仅当「当前不是演示模式」且「与部署方默认凭据不同」时才值得回退。
    """
    if creds.demo:
        return None
    base = default_creds()
    if base.demo:
        return None
    if (base.llm_key, base.vision_key, base.img_key) == (
        creds.llm_key,
        creds.vision_key,
        creds.img_key,
    ):
        return None  # 本来就用的是默认凭据，重试无意义
    return base


def creds_chain(creds: Creds) -> list[Creds]:
    """凭据尝试顺序：用户私有 → 部署方默认（去重）。

    用于"用户自己的 Key 失效/欠费时，不至于直接掉到演示数据"。
    """
    fb = fallback_creds(creds)
    return [creds, fb] if fb else [creds]


def providers_for_user(user_id: int | None) -> list[dict]:
    """厂商列表（按账号视角）：available = 自己有 Key 或部署方有 Key。"""
    ukeys: set[str] = set()
    if user_id:
        from . import db

        ukeys = set(db.user_keys(user_id))
    active = creds_for_user(user_id).provider
    return [
        {
            "id": pid,
            "name": p["name"],
            "available": pid in ukeys or pid in KEYS,
            "mine": pid in ukeys,
            "active": pid == active,
            "signup_url": p.get("signup_url", ""),
            "text_model": p["text_model"],
            "vision_model": p["vision_model"],
            "img_model": p["img_model"],
            "note": p["note"],
        }
        for pid, p in PROVIDERS.items()
    ]


def snapshot_for_user(user_id: int | None) -> dict:
    """当前引擎状态（按账号视角），/api/providers 与切换接口统一返回。"""
    creds = creds_for_user(user_id)
    return {
        "active": creds.provider,
        "demo": creds.demo,
        "providers": providers_for_user(user_id),
    }


def _clean_key(key: str) -> str:
    """校验并规范化 API Key（必须单行且 ≤200 字符，防止污染存储）。"""
    key = (key or "").strip()
    if not key:
        raise ValueError("API Key 不能为空")
    if any(ch in key for ch in "\r\n") or len(key) > 200:
        raise ValueError("API Key 格式不正确（应为单行、长度不超过 200）")
    return key


def register_user_key(user_id: int, pid: str, key: str) -> dict:
    """把 Key 登记到【当前账号】名下（只影响该账号，不写 .env、不影响他人）。"""
    if pid not in PROVIDERS:
        raise KeyError(pid)
    key = _clean_key(key)
    from . import db

    db.set_user_key(user_id, pid, key)
    return snapshot_for_user(user_id)


def set_user_provider(user_id: int, pid: str) -> dict:
    """设置【当前账号】偏好的厂商；该账号与部署方都无 Key 时抛 PermissionError。"""
    if pid not in PROVIDERS:
        raise KeyError(pid)
    from . import db

    if pid not in db.user_keys(user_id) and pid not in KEYS:
        raise PermissionError(f"厂商 {pid} 未配置 API Key，请先接入你自己的 Key")
    db.set_user_active_provider(user_id, pid)
    return snapshot_for_user(user_id)


def remove_user_key(user_id: int, pid: str) -> dict:
    """移除【当前账号】在某厂商下的私有 Key（可撤销误接入的 Key）。"""
    if pid not in PROVIDERS:
        raise KeyError(pid)
    from . import db

    db.delete_user_key(user_id, pid)
    # 偏好若指向已删除的厂商，清空它，避免悬空指向
    if db.user_active_provider(user_id) == pid:
        db.set_user_active_provider(user_id, "")
    return snapshot_for_user(user_id)
