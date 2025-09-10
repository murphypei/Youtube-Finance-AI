# 基于PyTorch官方镜像，支持CUDA GPU加速
FROM pytorch/pytorch:2.1.0-cuda11.8-cudnn8-devel

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV CUDA_VISIBLE_DEVICES=0
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Asia/Shanghai

# 配置使用阿里云镜像源以提高下载速度和稳定性
RUN sed -i 's/archive.ubuntu.com/mirrors.aliyun.com/g' /etc/apt/sources.list && \
    sed -i 's/security.ubuntu.com/mirrors.aliyun.com/g' /etc/apt/sources.list

# 更新系统并安装必要的系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    curl \
    git \
    ffmpeg \
    build-essential \
    tzdata \
    && ln -fs /usr/share/zoneinfo/Asia/Shanghai /etc/localtime \
    && dpkg-reconfigure -f noninteractive tzdata \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 升级pip并安装依赖（优化层缓存）
RUN pip install --upgrade pip && \
    pip install openai-whisper && \
    pip install google-genai google-api-core && \
    pip install jupyter notebook ipywidgets && \
    pip install flask pandas matplotlib seaborn plotly

# 复制并安装项目依赖（先复制不经常变化的文件）
COPY pyproject.toml .
RUN pip install -e .

# 复制源代码（最后复制，避免代码变化影响前面的缓存）
COPY core/ ./core/
COPY tools/ ./tools/
COPY web/ ./web/
COPY run_app.py ./
COPY prompts/ ./prompts/
COPY config/ ./config/

# 创建必要目录并预下载模型
RUN mkdir -p /app/downloads /app/downloads && \
    python -c "import whisper; whisper.load_model('base')"

# 暴露端口
EXPOSE 8850
EXPOSE 8851
EXPOSE 8852

# 设置默认命令
CMD ["python", "run_app.py", "single"]
