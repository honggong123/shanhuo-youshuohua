"""打包《山货有话说》参赛提交包。

产物：D:/比赛2/交付物/山货有话说-参赛作品源码.zip

竞赛表单第 10 项要求：
  「除承诺书、截图、视频和PPT以外文件压缩打包成1个压缩文件」
故本包**必须排除**这四类，它们各自是表单的独立提交项。

包含：源码 + 文档 + 素材
排除：PPT/截图/视频（表单独立项）、开发过程产物（辅助脚本 / 本地 .bat / 内部笔记）、
      node_modules（可 npm install 还原）、运行期产物（generated/uploads/db）、
      .env（含 API Key）、各类缓存、压缩包本身

用法：
    python 交付物/pack_submission.py
"""
from __future__ import annotations

import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "交付物" / "山货有话说-参赛作品源码.zip"

# 整体排除的目录名（任意层级命中即跳过）
SKIP_DIRS = {
    "node_modules", "__pycache__", ".mimosa", ".git", ".idea", ".vscode",
    "generated", "uploads",                                  # 运行期产物
    ".workbuddy-ai",                                          # 助手工作目录
    ".zcode", ".zcode-ai",                                    # IDE 工作目录残留
    ".slidep",                                                # PPT 工具缓存
    "界面截图",                                                # 截图：表单独立提交项
    "山货有话说-答辩PPT",                                       # PPT：表单独立提交项
    "scripts",                                                 # 本地便利脚本（开机自启/防火墙等）
}

# 整体排除的文件名
SKIP_FILES = {
    ".env",                          # 含 API Key，绝不能提交
    "shanhuo.db",                    # 运行数据库
    ".gitignore", ".zcodeignore",
    "Thumbs.db", ".DS_Store",
}

# 明确排除的具体路径（相对项目根，POSIX 风格）
# 这些是「开发过程产物」而非「作品源码」，评委用不上。
# 注意：只从包里排除，本机文件保留，后续开发仍要用。
SKIP_PATHS = {
    # —— 打包 / 部署辅助脚本 ——
    "交付物/pack_submission.py",        # 打包脚本本身，装进包里是自我引用
    "交付物/generate_shuomingshu.py",   # 生成说明书的脚本，成品 .docx 已在包内
    "deploy/build_cloudrun_zip.py",
    "deploy/deploy_cloudrun.py",
    "deploy/nginx参考配置.conf",         # 未启用的备用部署方案
    # —— 本地便利脚本（只在本机跑项目时有用）——
    # 2026-10-10 整理：4 个低频 .bat 已从根目录移入 scripts/（启动.bat 保留在根目录）
    "scripts/启动后台.bat",
    "scripts/一键设置开机自启.bat",
    "scripts/取消开机自启.bat",
    "scripts/开放防火墙端口.bat",
    # —— 内部笔记（开发过程记录）——
    "deploy/部署上线指南.md",            # 含云托管环境 ID 等内部信息
    "交付物/演示视频录制脚本.md",
    "素材/拍摄清单.md",
}

# 整体排除的后缀
#   .zip/.rar/.7z 压缩包本身；.log 日志
#   .ppt/.pptx 演示文稿、.mp4/.mov/.avi/.mkv 视频 —— 均为表单独立提交项
#   .png/.jpg 截图类不放这里，避免误伤 test_images/ 等源码素材，改用目录名排除
SKIP_SUFFIX = {
    ".pyc", ".pyo", ".zip", ".rar", ".7z", ".log",
    ".ppt", ".pptx", ".pps", ".ppsx",
    ".mp4", ".mov", ".avi", ".mkv", ".wmv", ".flv",
}

# 排除的文件大小下限之外还要跳过的临时文件模式
SKIP_NAME_PREFIX = ("~$", ".~")


def should_skip(rel: Path) -> str | None:
    """返回跳过原因，None 表示保留。"""
    if rel.as_posix() in SKIP_PATHS:
        return "开发过程产物"
    if any(part in SKIP_DIRS for part in rel.parts):
        return "目录"
    if rel.name in SKIP_FILES:
        return "敏感/运行期文件"
    if rel.suffix.lower() in SKIP_SUFFIX:
        return "后缀过滤"
    if rel.name.startswith(SKIP_NAME_PREFIX):
        return "临时文件"
    return None


def main() -> int:
    if not ROOT.exists():
        print(f"[x] 项目根不存在: {ROOT}")
        return 1

    kept: list[tuple[Path, str]] = []
    skipped: dict[str, int] = {}

    for f in sorted(ROOT.rglob("*")):
        if not f.is_file():
            continue
        rel = f.relative_to(ROOT)
        reason = should_skip(rel)
        if reason:
            skipped[reason] = skipped.get(reason, 0) + 1
            continue
        kept.append((f, rel.as_posix()))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    if OUT.exists():
        OUT.unlink()

    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for src, arc in kept:
            zf.write(src, arc)

    size_mb = OUT.stat().st_size / 1024 / 1024
    print("=" * 60)
    print(f"[ok] 已生成 {OUT}")
    print(f"     体积 {size_mb:.2f} MB   文件数 {len(kept)}")
    print("=" * 60)
    print("\n排除统计：")
    for k, v in sorted(skipped.items(), key=lambda x: -x[1]):
        print(f"  {k:<16} {v} 项")

    print("\n按路径排除的开发过程产物（本机文件保留）：")
    for p in sorted(SKIP_PATHS):
        mark = "x" if (ROOT / p).exists() else "?"
        print(f"  [{mark}] {p}")

    print("\n包含的顶层目录/文件：")
    tops: dict[str, int] = {}
    for _, arc in kept:
        top = arc.split("/")[0]
        tops[top] = tops.get(top, 0) + 1
    for k, v in sorted(tops.items()):
        print(f"  {k:<24} {v} 个文件")

    # 安全自检：确认敏感文件与「表单独立提交项」都未混入
    print("\n安全自检：")
    names = [a for _, a in kept]
    lower = [n.lower() for n in names]
    checks = [
        (".env 未混入", not any(n.endswith("/.env") or n == ".env" for n in names)),
        ("node_modules 未混入", not any("node_modules" in n for n in names)),
        ("generated 未混入", not any(n.startswith("backend/generated/") for n in names)),
        ("db 未混入", not any(n.endswith(".db") for n in names)),
        ("压缩包未混入", not any(n.endswith(".zip") for n in names)),
        ("PPT 未混入", not any(n.endswith((".ppt", ".pptx", ".pps", ".ppsx")) for n in lower)
                      and not any("答辩PPT" in n for n in names)),
        ("截图 未混入", not any("界面截图" in n for n in names)),
        ("视频 未混入", not any(n.endswith((".mp4", ".mov", ".avi", ".mkv", ".wmv", ".flv")) for n in lower)),
    ]
    ok = True
    for label, passed in checks:
        print(f"  {'✅' if passed else '❌'} {label}")
        ok = ok and passed

    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
