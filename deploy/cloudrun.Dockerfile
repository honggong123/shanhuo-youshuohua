# 《山货有话说》后端镜像 —— 微信云托管「上传代码包」专用
#
# 对应的上传包结构（deploy/build_cloudrun_zip.py 自动生成）：
#   Dockerfile
#   requirements.txt
#   app/**
#
# 注意：云托管通过 PORT 环境变量注入监听端口，控制台「服务设置 → 端口」保持默认 80 即可。
FROM python:3.12-slim

WORKDIR /app

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

EXPOSE 80

CMD ["sh", "-c", "python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-80}"]
