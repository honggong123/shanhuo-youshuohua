"""文创海报合成：
1. 若配置了文生图 key → 生成国潮风底图，再用 PIL 排版文字（保证中文不乱码）；
2. 否则 → 本地渐变模板 + 产品照片 + 文字排版，完全离线可用。
"""
import base64
import hashlib
import io
import uuid
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from .. import config

W, H = 900, 1200
GENERATED = config.GENERATED_DIR / "poster"

# 中文字体候选（按平台顺序尝试）。
# Linux 一档是云托管/云服务器必需的：slim 镜像默认不含中文字体，
# 缺字体会让海报上的中文变成方块（tofu）。deploy/cloudrun.Dockerfile 已装 fonts-noto-cjk。
BOLD_CANDIDATES = [
    # Linux
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc",
    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
    # macOS
    "/System/Library/Fonts/PingFang.ttc",
    "/System/Library/Fonts/STHeiti Medium.ttc",
    # Windows
    r"C:\Windows\Fonts\msyhbd.ttc",
    r"C:\Windows\Fonts\simhei.ttf",
]
REGULAR_CANDIDATES = [
    # Linux
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc",
    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
    # macOS
    "/System/Library/Fonts/PingFang.ttc",
    "/System/Library/Fonts/STHeiti Light.ttc",
    # Windows
    r"C:\Windows\Fonts\msyh.ttc",
    r"C:\Windows\Fonts\simsun.ttc",
]

_font_warned = False

THEMES = [
    {"deep": (46, 94, 62), "mid": (94, 158, 94), "light": (244, 246, 230)},
    {"deep": (158, 92, 42), "mid": (222, 158, 84), "light": (250, 242, 226)},
    {"deep": (52, 84, 116), "mid": (96, 148, 178), "light": (236, 246, 250)},
]


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    global _font_warned
    for p in (BOLD_CANDIDATES if bold else REGULAR_CANDIDATES):
        if Path(p).exists():
            try:
                return ImageFont.truetype(p, size)
            except OSError:
                continue
    if not _font_warned:
        _font_warned = True
        print("[warn] 未找到中文字体，海报中文可能显示为方块。"
              "容器内请安装 fonts-noto-cjk（见 deploy/cloudrun.Dockerfile）。")
    return ImageFont.load_default(size)


def _cover(img: Image.Image, w: int, h: int) -> Image.Image:
    scale = max(w / img.width, h / img.height)
    img = img.resize((round(img.width * scale), round(img.height * scale)))
    x, y = (img.width - w) // 2, (img.height - h) // 2
    return img.crop((x, y, x + w, y + h))


def _decode_b64(s: str) -> Image.Image:
    if "," in s and s.strip().startswith("data:"):
        s = s.split(",", 1)[1]
    return Image.open(io.BytesIO(base64.b64decode(s))).convert("RGB")


def _gradient(theme) -> Image.Image:
    img = Image.new("RGB", (W, H))
    top, mid, bottom = theme["light"], theme["mid"], theme["deep"]
    for y in range(H):
        t = y / H
        if t < 0.55:
            k = t / 0.55
            c = tuple(round(top[i] + (mid[i] - top[i]) * k) for i in range(3))
        else:
            k = (t - 0.55) / 0.45
            c = tuple(round(mid[i] + (bottom[i] - mid[i]) * k) for i in range(3))
        ImageDraw.Draw(img).line([(0, y), (W, y)], fill=c)
    return img


def _wrap(text: str, font: ImageFont.FreeTypeFont, max_w: int) -> list[str]:
    d = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    lines, cur = [], ""
    for ch in text:
        if d.textlength(cur + ch, font=font) > max_w and cur:
            lines.append(cur)
            cur = ch
        else:
            cur += ch
    if cur:
        lines.append(cur)
    return lines


def _rounded_mask(w: int, h: int, radius: int) -> Image.Image:
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, w, h], radius=radius, fill=255)
    return m


def _text_shadow(d, pos, text: str, font, fill, shadow=(0, 0, 0, 120), off=3):
    x, y = pos
    d.text((x + off, y + off), text, font=font, fill=shadow)
    d.text((x, y), text, font=font, fill=fill)


def _ai_art(name: str, origin: str) -> Image.Image | None:
    if not config.IMG_API_KEY or not config.IMG_MODEL:
        return None
    prompt = (
        f"中国风文创宣传海报背景插画，主体是{name}，{origin}的乡土元素，"
        "国潮插画风格，柔和暖色调，大量留白构图，画面纯净无任何文字无水印，竖版"
    )
    try:
        from openai import OpenAI

        client = OpenAI(api_key=config.IMG_API_KEY, base_url=config.IMG_BASE_URL, timeout=120)
        resp = client.images.generate(
            model=config.IMG_MODEL, prompt=prompt,
            size=config.IMG_SIZE or "768x1344", n=1,
            response_format="b64_json",
        )
        item = resp.data[0]

        # OpenAI 系返回 b64_json；智谱 CogView 等会**静默忽略** response_format 只给 url，
        # 因此必须两条路都支持，否则 AI 底图会无声无息地降级成本地模板。
        b64 = getattr(item, "b64_json", None)
        if b64:
            return Image.open(io.BytesIO(base64.b64decode(b64))).convert("RGB")

        url = getattr(item, "url", None)
        if url:
            import httpx

            raw = httpx.get(url, timeout=120).content
            return Image.open(io.BytesIO(raw)).convert("RGB")
        return None
    except Exception:
        return None


def compose(image_b64: str, name: str, tagline: str, origin: str) -> tuple[Path, bool]:
    """返回 (海报文件路径, 是否使用了 AI 底图)。"""
    GENERATED.mkdir(exist_ok=True)
    theme = THEMES[int(hashlib.sha256(name.encode()).hexdigest(), 16) % len(THEMES)]
    seed = int(hashlib.sha256(("dots:" + name).encode()).hexdigest(), 16)

    art = _ai_art(name, origin)
    if art is not None:
        base = _cover(art, W, H)
        ai = True
    else:
        base = _gradient(theme)
        ai = False
        photo = _cover(_decode_b64(image_b64), W - 120, 620)
        base.paste(photo, (60, 90), _rounded_mask(*photo.size, 36))

    base = base.convert("RGBA")

    # 底部压暗渐变，保证文字可读
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    for y in range(H - 460, H):
        k = (y - (H - 460)) / 460
        od.line([(0, y), (W, y)], fill=(20, 24, 18, round(190 * k)))
    base = Image.alpha_composite(base, overlay)
    d = ImageDraw.Draw(base)

    # 品牌角标
    badge_f = _font(30, bold=True)
    badge_txt = "山货有话说 · AI助农"
    bw = d.textlength(badge_txt, font=badge_f) + 56
    d.rounded_rectangle([36, 36, 36 + bw, 96], radius=30, fill=(0, 0, 0, 110))
    d.text((64, 52), badge_txt, font=badge_f, fill=(255, 255, 255, 235))

    # 产地徽章
    if origin:
        of = _font(28)
        otxt = f"产地 · {origin}"
        d.rounded_rectangle([60, H - 396, 60 + d.textlength(otxt, font=of) + 40, H - 346],
                            radius=25, fill=(255, 255, 255, 200))
        d.text((80, H - 387), otxt, font=of, fill=(40, 52, 40, 255))

    # 标题与标语
    tf = _font(88, bold=True)
    tlines = _wrap(name, tf, W - 120)[:2]
    ty = H - 300
    for ln in tlines:
        _text_shadow(d, (58, ty), ln, tf, (255, 255, 255, 255))
        ty += 104

    if tagline:
        sf = _font(34)
        for ln in _wrap(tagline, sf, W - 130)[:2]:
            _text_shadow(d, (62, ty + 12), ln, sf, (255, 246, 220, 240))
            ty += 50

    # 装饰圆点（位置由产品名哈希决定，保证同名海报样式一致）
    for i in range(6):
        x = 20 + (seed >> (i * 6)) % (W - 40)
        y = 20 + (seed >> (i * 6 + 3)) % (H - 540)
        r = 4 + (seed >> (i * 5 + 1)) % 11
        d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 255, 255, 40))

    out = GENERATED / f"poster_{uuid.uuid4().hex[:10]}.jpg"
    base.convert("RGB").save(out, quality=90)
    from ..files import prune_dir

    prune_dir(GENERATED, keep=200)
    return out, ai
