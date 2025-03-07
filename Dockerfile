# 使用Python 3.9作为基础镜像
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TZ=Asia/Shanghai \
    CONFIG_PATH=/config/config.json

# 安装基本工具（包括curl用于健康检查）
RUN apt-get update && apt-get install -y curl && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# 复制依赖文件并安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用程序代码
COPY *.py .

# 创建配置文件目录
RUN mkdir -p /config

# 提供默认配置作为示例
COPY config.json /config/config.json.example

# 暴露API端口
EXPOSE 8000

# 设置健康检查
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/ || exit 1

# 设置容器启动命令
CMD ["python", "main.py"] 