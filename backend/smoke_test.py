"""冒烟测试：演示模式下跑通全部接口（不含真实 AI 调用）。"""
import io

from PIL import Image, ImageDraw
from fastapi.testclient import TestClient

from app.main import app

c = TestClient(app)

# 造一张测试图
img = Image.new("RGB", (640, 480), (220, 140, 60))
ImageDraw.Draw(img).ellipse([180, 100, 460, 380], fill=(255, 190, 80))
buf = io.BytesIO()
img.save(buf, "JPEG")
import base64
b64 = base64.b64encode(buf.getvalue()).decode()

print("health:", c.get("/api/health").json())

r = c.post("/api/recognize", json={"image": b64})
print("recognize:", r.status_code, r.json()["name"], "demo =", r.json()["demo"])

g = c.post("/api/generate", json={"name": "富平柿饼", "category": "果干", "origin": "陕西富平",
                                  "highlights": ["霜白肉红"]})
print("generate:", g.status_code, g.json()["title"])

p = c.post("/api/poster", json={"image": b64, "name": "富平柿饼", "tagline": "一口流蜜的千年柿乡", "origin": "陕西富平"})
print("poster:", p.status_code, p.json())

t = c.post("/api/tts", json={"text": "大家好，这是富平柿饼的语音介绍测试。"})
print("tts:", t.status_code, t.json() if t.status_code == 200 else t.json())

v = c.get("/api/villages")
print("villages:", v.status_code, len(v.json()), "个村落")

gd = c.post("/api/guide", json={"village_id": "yucun"})
print("guide:", gd.status_code, gd.json()["village"], gd.json()["story"][:20], "...")
