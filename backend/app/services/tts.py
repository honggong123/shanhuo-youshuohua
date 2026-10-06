"""Edge-TTS 语音合成（免费，无需 key）。"""
import uuid

import edge_tts

from .. import config

GENERATED = config.GENERATED_DIR / "audio"
MAX_LEN = 600


async def synthesize(text: str, voice: str = "") -> str:
    GENERATED.mkdir(exist_ok=True)
    text = text.strip()[:MAX_LEN]
    if not text:
        raise ValueError("文本为空")
    out = GENERATED / f"tts_{uuid.uuid4().hex[:10]}.mp3"
    communicate = edge_tts.Communicate(text, voice or config.TTS_VOICE)
    await communicate.save(str(out))
    return out
