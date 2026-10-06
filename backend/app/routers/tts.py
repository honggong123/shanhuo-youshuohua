"""语音合成接口。"""
import edge_tts
from fastapi import APIRouter, HTTPException

from .. import config
from ..schemas import TtsIn, TtsOut
from ..services import tts as tts_service

router = APIRouter()


@router.post("/api/tts", response_model=TtsOut)
async def make_tts(body: TtsIn):
    try:
        path = await tts_service.synthesize(body.text, body.voice)
    except edge_tts.exceptions.NoAudioReceived:
        raise HTTPException(status_code=503, detail="语音服务暂不可用，请稍后再试")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"语音合成失败：{e}")
    return TtsOut(url=f"/static/audio/{path.name}", voice=body.voice or config.TTS_VOICE)
