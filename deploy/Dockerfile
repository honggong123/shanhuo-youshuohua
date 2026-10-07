# 《山货有话说》后端容器镜像（微信云托管 / 任意云服务器通用）
FROM python:3.12-slim

WORKDIR /app

# 先装依赖，利用 Docker 层缓存
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 拷贝后端代码
COPY backend/ .

# 运行时环境变量（在云托管控制台或 docker run -e 配置，勿写进镜像）：
#   DEEPSEEK_API_KEY / GLM_API_KEY ...   模型 Key
#   TTS_VOICE / HOST / PORT              可选
EXPOSE 8000

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
