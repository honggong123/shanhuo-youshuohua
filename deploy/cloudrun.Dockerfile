# 《山货有话说》后端镜像 —— 微信云托管「上传代码包」专用
#
# 对应的上传包结构（deploy/build_cloudrun_zip.py 自动生成）：
#   Dockerfile
#   requirements.txt
#   app/**
#   frontend/dist/**      <- 网页版静态产物，由后端 main.py 统一托管
#
# 注意：云托管通过 PORT 环境变量注入监听端口，控制台「服务设置 → 端口」保持默认 80 即可。
FROM python:3.12-slim

# 目录选择说明（很重要）：
# config.py 里 BACKEND_DIR = Path(__file__).resolve().parent.parent
#   - 若工作目录是 /app，则 __file__=/app/config.py → BACKEND_DIR=/app → 正确
#   - 但 main.py 的 FRONTEND_DIST = BACKEND_DIR.parent/"frontend"/"dist" 会算成 /frontend/dist
# 为让「运行时写目录（generated/uploads）」和「前端产物」都落在同一可写根下，
# 统一采用 /srv 作为工作根：/srv/app + /srv/frontend/dist
WORKDIR /srv

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# 中文字体：海报排版用 PIL 直接写字，slim 镜像不带中文字体会渲染成方块
RUN apt-get update \
 && apt-get install -y --no-install-recommends fonts-noto-cjk \
 && rm -rf /var/lib/apt/lists/*

# 必须先 COPY 依赖清单再安装，否则 pip 找不到 requirements.txt 直接构建失败
COPY requirements.txt .
RUN pip install -r requirements.txt -i https://mirrors.cloud.tencent.com/pypi/simple

COPY app/ ./app/
# frontend/dist 由 build_cloudrun_zip.py 保证一定存在（缺构建产物时放 .keep 占位），
# 否则这里的无条件 COPY 会让镜像构建失败。
COPY frontend/dist/ ./frontend/dist/

EXPOSE 80

CMD ["sh", "-c", "cd /srv && python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-80}"]
