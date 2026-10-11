"""打包《山货有话说》后端为微信云托管「上传代码包」。

产物：deploy/backend_cloudrun.zip
结构（顶层即构建上下文根，云托管会直接读根目录的 Dockerfile）：
    Dockerfile            <- 取自 deploy/cloudrun.Dockerfile
    requirements.txt      <- 取自 backend/requirements.txt
    app/**                <- 取自 backend/app/（剔除 __pycache__ / *.pyc）
    frontend/dist/**      <- 取自 frontend/dist/（网页版静态产物，可选）

用法：
    python deploy/build_cloudrun_zip.py
"""
from __future__ import annotations

import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BACKEND = ROOT / "backend"
OUT = ROOT / "deploy" / "backend_cloudrun.zip"
DOCKERFILE = ROOT / "deploy" / "cloudrun.Dockerfile"

SKIP_DIRS = {"__pycache__"}
SKIP_SUFFIX = {".pyc", ".pyo"}


def main() -> int:
    for p in (BACKEND / "requirements.txt", BACKEND / "app", DOCKERFILE):
        if not p.exists():
            print(f"[x] 缺少必要路径: {p}")
            return 1

    # 网页版产物：缺失时只警告不中止（小程序走 API，不依赖网页版）
    dist = ROOT / "frontend" / "dist"
    if not dist.exists() or not (dist / "index.html").exists():
        print(f"[!] 未找到前端构建产物 {dist}，将跳过网页版")
        print("    如需一并部署网页版，请先在 frontend/ 目录执行：npm install && npm run build")
        dist = None

    entries: list[tuple[Path, str]] = [(DOCKERFILE, "Dockerfile")]
    entries.append((BACKEND / "requirements.txt", "requirements.txt"))
    for f in sorted((BACKEND / "app").rglob("*")):
        if not f.is_file():
            continue
        if any(part in SKIP_DIRS for part in f.parts):
            continue
        if f.suffix in SKIP_SUFFIX:
            continue
        entries.append((f, f"app/{f.relative_to(BACKEND / 'app').as_posix()}"))

    if dist is not None:
        for f in sorted(dist.rglob("*")):
            if not f.is_file():
                continue
            entries.append((f, f"frontend/dist/{f.relative_to(dist).as_posix()}"))

    if OUT.exists():
        OUT.unlink()
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for src, arc in entries:
            zf.write(src, arc)
        if dist is None:
            # cloudrun.Dockerfile 里 `COPY frontend/dist/` 是无条件的，缺目录会直接
            # 让镜像构建失败。放一个占位文件保证构建可过；此时网页版不可用，
            # 但小程序走 API，不受影响。
            zf.writestr("frontend/dist/.keep", "")

    size_kb = OUT.stat().st_size / 1024
    print(f"[ok] 已生成 {OUT}  ({size_kb:.1f} KB, {len(entries)} 个文件)")
    for _, arc in entries:
        if not arc.startswith("frontend/") or arc.count("/") <= 2:
            print("     ", arc)
    n_front = sum(1 for _, a in entries if a.startswith("frontend/"))
    if n_front:
        print(f"      frontend/dist/... （共 {n_front} 个文件）")
    else:
        print("      frontend/dist/.keep （占位，网页版未打包，仅 API 可用）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
