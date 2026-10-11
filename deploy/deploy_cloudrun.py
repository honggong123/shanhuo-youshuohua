"""《山货有话说》微信云托管一键部署。

前提：已在微信开发者工具里开通「云托管环境」并扫码成功。

用法：
    python deploy/deploy_cloudrun.py                    # 交互式
    python deploy/deploy_cloudrun.py --env <环境ID>      # 指定环境
    python deploy/deploy_cloudrun.py --dry-run          # 只打印将执行的命令

流程：登录态校验 → 查环境 → 建服务 → 上传代码包 → 输出验证清单
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ZIP = ROOT / "deploy" / "backend_cloudrun.zip"
MINIPROGRAM = ROOT / "miniprogram"

CLI = r"D:\微信\微信web开发者工具\cli.bat"
WXCLOUD = r"C:\Users\usa\.workbuddy-ai\binaries\node\workspace\node_modules\.bin\wxcloud.cmd"

# 云托管控制台「服务设置」要填的环境变量。
# 值留空表示「从本机 backend/.env 复制」——脚本会读取并打印提示，但敏感值不落盘。
ENV_KEYS = [
    "GLM_API_KEY",
    "DEEPSEEK_API_KEY",
    "QWEN_API_KEY",
    "MOONSHOT_API_KEY",
    "OPENAI_API_KEY",
    "DEFAULT_PROVIDER",
    "TTS_VOICE",
]


def run(cmd: list[str], label: str, dry: bool = False) -> int:
    print(f"\n>>> {label}")
    print("    " + " ".join(cmd))
    if dry:
        return 0
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=600)
    except subprocess.TimeoutExpired:
        print("    [x] 超时（600s）")
        return 1
    out = (p.stdout or "") + (p.stderr or "")
    # 过滤开发者工具的噪音
    for line in out.splitlines():
        if any(k in line for k in ("crashpad", "DeprecationWarning", "trace-deprecation")):
            continue
        if line.strip():
            print("    " + line)
    print(f"    [exit {p.returncode}]")
    return p.returncode


def read_local_env() -> dict[str, str]:
    f = ROOT / "backend" / ".env"
    if not f.exists():
        return {}
    out: dict[str, str] = {}
    for raw in f.read_text(encoding="utf-8").splitlines():
        s = raw.strip()
        if not s or s.startswith("#") or "=" not in s:
            continue
        k, _, v = s.partition("=")
        out[k.strip()] = v.strip()
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--env", help="云托管环境 ID（不传则自动取第一个）")
    ap.add_argument("--dry-run", action="store_true", help="只打印命令不执行")
    args = ap.parse_args()
    dry = args.dry_run

    print("=" * 64)
    print("《山货有话说》微信云托管部署")
    print("=" * 64)

    # 0. 前置检查
    if not ZIP.exists():
        print("[x] 找不到上传包，请先运行：python deploy/build_cloudrun_zip.py")
        return 1
    print(f"[ok] 上传包 {ZIP.name}  {ZIP.stat().st_size / 1024:.1f} KB")

    env_local = read_local_env()
    print("\n[环境变量] 部署后请在控制台「服务设置」填入以下项：")
    for k in ENV_KEYS:
        v = env_local.get(k, "")
        mark = "✓ 本机有值" if v else "· 本机为空"
        print(f"    {k:<20} {mark}")
    print("    PORT=80           （与 Dockerfile 保持一致）")
    print("    HOST=0.0.0.0      （容器内必须监听全网卡）")

    # 1. 登录态
    rc = run([CLI, "islogin", "--project", str(MINIPROGRAM)], "检查开发者工具登录态", dry)
    if rc != 0 and not dry:
        print("\n[x] 未登录。请打开微信开发者工具扫码登录后重试。")
        return 1

    # 2. 列出环境
    print("\n" + "-" * 64)
    rc = run([CLI, "cloud", "env", "list", "--project", str(MINIPROGRAM)],
             "查询云环境（应至少有一个云托管环境）", dry)
    if rc != 0 and not dry:
        print("\n[x] 查询环境失败。")
        return 1

    print("\n" + "=" * 64)
    print("接下来（CLI 能力有限，以下步骤需在云托管控制台点几下）：")
    print("=" * 64)
    print("""
1. 打开 https://cloud.weixin.qq.com/cloudrun
2. 「服务管理」→「新建服务」
   - 服务名建议：shanhuo-api
   - 部署方式选「上传代码包」
3. 上传：deploy/backend_cloudrun.zip
4. 「服务设置」→ 端口填 80
5. 「服务设置」→ 环境变量按上面清单填写，DEFAULT_PROVIDER=glm
6. 「公网访问」→ 开启，拿到域名
7. 浏览器打开 <域名>/api/health
        ✅ {"ok":true,"demo":false}  → 部署成功
        ⚠️ {"ok":true,"demo":true}   → 环境变量没配进去
        ❌ 502 / 打不开               → 端口不一致，回第 4 步
8. 把域名填进 miniprogram/config.js 的 BASE_URL（末尾不带 /）

提示：脚本已把本机能读到的 Key 状态列在上面，复制时别漏。
      .env 里的值不要提交进 git 仓库。
""")
    return 0


if __name__ == "__main__":
    sys.exit(main())
