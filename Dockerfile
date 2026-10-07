# 《山货有话说》后端容器镜像 —— 微信云托管版
# 云托管要求服务监听它指定的端口（默认 9000），通过 PORT 环境变量注入
FROM python:3.12-slim

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .

EXPOSE 9000

# 云托管通过 PORT 环境变量指定监听端口，默认 9000
CMD ["sh", "-c", "python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-9000}"]
