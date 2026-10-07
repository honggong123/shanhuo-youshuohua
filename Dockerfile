# 《山货有话说》后端容器镜像 —— 仓库根目录构建（云服务器 / 微信云托管「Git 仓库构建」）
# 云托管通过 PORT 环境变量注入监听端口；云服务器上可直接 -e PORT=8000
FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# 中文字体：海报排版用 PIL 直接写字，slim 镜像不带中文字体会渲染成方块
RUN apt-get update \
 && apt-get install -y --no-install-recommends fonts-noto-cjk \
 && rm -rf /var/lib/apt/lists/*

# 使用腾讯云内网 PyPI 镜像，构建快且稳定
COPY backend/requirements.txt .
RUN pip install -r requirements.txt -i https://mirrors.cloud.tencent.com/pypi/simple

COPY backend/ .

EXPOSE 8000

CMD ["sh", "-c", "python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
