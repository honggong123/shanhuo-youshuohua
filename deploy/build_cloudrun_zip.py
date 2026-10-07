"""打包《山货有话说》后端为微信云托管「上传代码包」。

产物：deploy/backend_cloudrun.zip
结构（顶层即构建上下文根，云托管会直接读根目录的 Dockerfile）：
    Dockerfile            <- 取自 deploy/cloudrun.Dockerfile
    requirements.txt      <- 取自 backend/requirements.txt
    app/**                <- 取自 backend/app/（剔除 __pycache__ / *.pyc）

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

    if OUT.exists():
        OUT.unlink()
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for src, arc in entries:
            zf.write(src, arc)

    size_kb = OUT.stat().st_size / 1024
    print(f"[ok] 已生成 {OUT}  ({size_kb:.1f} KB, {len(entries)} 个文件)")
    for _, arc in entries:
        print("     ", arc)
    return 0


if __name__ == "__main__":
    sys.exit(main())
