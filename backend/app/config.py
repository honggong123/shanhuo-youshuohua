"""读取 .env 配置；支持多厂商 Key 与运行时动态切换。

- 各厂商 Key 在 .env 中按 providers.py 约定的环境变量名配置；
- 兼容旧配置：单一 LLM_API_KEY 视为智谱 GLM 的 Key；
- DEFAULT_PROVIDER 指定默认厂商（auto = 第一个有 Key 的厂商）；
- 未配置任何 Key 时自动进入演示模式（DEMO_MODE = True）。
"""
import os
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

FRONTEND_DIST = BACKEND_DIR.parent / "frontend" / "dist"


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


def _apply(pid: str | None) -> None:
    """把厂商 pid 的连接信息应用到当前配置；pid 为 None 时进入演示模式。"""
    global ACTIVE_PROVIDER, DEMO_MODE
    global LLM_API_KEY, LLM_BASE_URL, LLM_MODEL
    global VISION_API_KEY, VISION_BASE_URL, VISION_MODEL
    global IMG_API_KEY, IMG_BASE_URL, IMG_MODEL

    if pid is None or pid not in KEYS:
        ACTIVE_PROVIDER = None
        DEMO_MODE = True
        LLM_API_KEY = LLM_BASE_URL = LLM_MODEL = ""
        VISION_API_KEY = VISION_BASE_URL = VISION_MODEL = ""
        IMG_API_KEY = IMG_BASE_URL = IMG_MODEL = ""
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


_apply(_default_pid)


def available_providers() -> list[dict]:
    """厂商列表，供前端展示与切换。"""
    return [
        {
            "id": pid,
            "name": p["name"],
            "available": pid in KEYS,
            "active": pid == ACTIVE_PROVIDER,
            "signup_url": p.get("signup_url", ""),
            "text_model": p["text_model"],
            "vision_model": p["vision_model"],
            "img_model": p["img_model"],
            "note": p["note"],
        }
        for pid, p in PROVIDERS.items()
    ]


def switch_provider(pid: str) -> dict:
    """切换到指定厂商。厂商不存在抛 KeyError；未配置 Key 抛 PermissionError。"""
    if pid not in PROVIDERS:
        raise KeyError(pid)
    if pid not in KEYS:
        raise PermissionError(f"厂商 {pid} 未配置 API Key，请在 backend/.env 中设置")
    _apply(pid)
    return {"active": ACTIVE_PROVIDER, "demo": DEMO_MODE}


def snapshot() -> dict:
    """当前引擎状态（/api/providers 与切换接口的统一返回）。"""
    return {
        "active": ACTIVE_PROVIDER,
        "demo": DEMO_MODE,
        "providers": available_providers(),
    }


def _save_key_env(pid: str, key: str) -> None:
    """把 Key 持久化到 backend/.env（更新对应行或追加），其余内容原样保留。"""
    env_name = PROVIDERS[pid]["key_env"]
    env_path = BACKEND_DIR / ".env"
    lines = env_path.read_text(encoding="utf-8").splitlines() if env_path.exists() else []
    out, found = [], False
    for ln in lines:
        if not found and ln.strip().startswith(f"{env_name}=") and not ln.strip().startswith("#"):
            out.append(f"{env_name}={key}")
            found = True
        else:
            out.append(ln)
    if not found:
        out.append(f"{env_name}={key}")
    env_path.write_text("\n".join(out) + "\n", encoding="utf-8")


def register_key(pid: str, key: str) -> dict:
    """登记（并持久化）一个新 Key，使其立即可用。厂商不存在抛 KeyError。"""
    if pid not in PROVIDERS:
        raise KeyError(pid)
    key = key.strip()
    if not key:
        raise ValueError("API Key 不能为空")
    KEYS[pid] = key
    _save_key_env(pid, key)
    return switch_provider(pid)
