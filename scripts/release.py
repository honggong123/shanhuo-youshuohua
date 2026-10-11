"""《山货有话说》一键发布：改完代码跑一次，把要同步的东西全部刷新。

三件产出（本脚本自动完成）：
    1) 网页版构建产物   frontend/dist                       （后端托管 + 进云托管上传包）
    2) 参赛提交包       交付物/山货有话说-参赛作品源码.zip      （竞赛表单第 10 项）
    3) 云托管上传包     deploy/backend_cloudrun.zip          （用于线上部署）

一件需人工（脚本只提醒）：
    - 线上部署：把 backend_cloudrun.zip 传到微信云托管控制台（CLI 不支持上传代码包）
    - 答辩 PPT：叙事内容（交付物/山货有话说-答辩PPT/slides/*.slide → .pptx），
      只在"关键数字/功能表述"变化时才需重做

用法：
    python scripts/release.py              # 全量（含前端构建）
    python scripts/release.py --no-build   # 跳过前端构建（dist 已是最新时）
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FRONTEND = ROOT / "frontend"
CLOUD_DOMAIN = "https://flask-plaf-324284-10-1501402795.sh.run.tcloudbase.com"


def run(cmd: list[str], label: str, cwd: Path = ROOT) -> None:
    print("\n" + "=" * 64)
    print(f">>> {label}")
    print("    " + " ".join(cmd))
    print("=" * 64)
    r = subprocess.run(cmd, cwd=str(cwd), shell=(os.name == "nt"))
    if r.returncode != 0:
        print(f"\n[x] 失败：{label}")
        sys.exit(r.returncode)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-build", action="store_true", help="跳过前端构建")
    args = ap.parse_args()

    print("《山货有话说》一键发布")
    print(f"项目根：{ROOT}")

    # 1) 前端构建
    if args.no_build:
        print("\n[skip] 前端构建（--no-build）")
    elif not (FRONTEND / "package.json").exists():
        print("\n[!] 未找到 frontend/package.json，跳过前端构建")
    elif not (FRONTEND / "node_modules").exists():
        print("\n[x] frontend/node_modules 不存在，请先执行：cd frontend && npm install")
        return 1
    else:
        run(["npm", "run", "build"], "1/3 构建网页版 → frontend/dist", cwd=FRONTEND)

    # 2) 参赛提交包
    run([sys.executable, str(ROOT / "交付物" / "pack_submission.py")], "2/3 生成参赛提交包")

    # 3) 云托管上传包
    run([sys.executable, str(ROOT / "deploy" / "build_cloudrun_zip.py")], "3/3 生成云托管上传包")

    print("\n" + "=" * 64)
    print("自动同步完成。以下两件需要人工确认：")
    print("=" * 64)
    print(f"""
【线上部署】把 deploy/backend_cloudrun.zip 上传到微信云托管：
  1. 打开 https://cloud.weixin.qq.com/cloudrun
  2. 服务 flask-plaf → 新建版本 → 上传代码包 → 选 deploy/backend_cloudrun.zip
  3. 「服务设置」端口填 80；环境变量沿用：
       GLM_API_KEY / DEFAULT_PROVIDER=glm / TTS_VOICE=zh-CN-XiaoxiaoNeural / PORT=80 / HOST=0.0.0.0
  4. 发布后验证 {CLOUD_DOMAIN}/api/health
       {{"ok":true,"demo":false}} → 成功

【答辩 PPT】只在"关键数字 / 功能表述"变化时才需重做：
  - 源文件：交付物/山货有话说-答辩PPT/slides/*.slide（叙事脚本见同目录 STORY.md）
  - 只改 bug / 实现细节 → 通常不用动；改了 KPI（村落数、耗时、功能名）→ 需同步更新
""")
    return 0


if __name__ == "__main__":
    sys.exit(main())
