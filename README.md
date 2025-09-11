# YouTube Finance AI

🎵 基于AI的YouTube财经视频分析工具，集成OpenAI Whisper语音转录和Google Gemini LLM智能分析，一键提取关键投资信息。

## 功能特性

- **🎬 YouTube媒体下载**: 支持高质量音频/视频提取
- **🎤 语音转录**: 基于OpenAI Whisper的高精度语音识别
- **🤖 AI财经分析**: 使用Google Gemini LLM深度提取关键投资信息
- **📊 智能信息提取**: 自动识别股票代码、价格点位、投资建议
- **📅 按日期组织**: 自动按日期归档所有结果文件
- **🐳 Docker化部署**: 开箱即用的Docker环境，支持GPU加速
- **🌐 Web仪表板**: 美观的网页界面展示分析结果

## 快速开始

### 1. 克隆项目
```bash
git clone <repository-url>
cd Youtube-Finance-AI
```

### 2. 配置Gemini LLM (可选)
```bash
cp config/gemini_config.json.template config/gemini_config.json
# 编辑config/gemini_config.json，填入你的Google Cloud凭据
```

### 3. 使用Docker运行 (推荐)
```bash
# 构建镜像
./docker-run.sh build

# 处理单个视频
./docker-run.sh process "https://www.youtube.com/watch?v=视频ID"

# 批量处理Rhino Finance频道
python run_app.py batch --limit 20

# 启动Web仪表板  
python -m web.web_dashboard
```

### 4. 直接运行
```bash
# 安装依赖
uv sync --extra whisper --extra gemini

# 处理单个视频
python run_app.py single "https://www.youtube.com/watch?v=视频ID"
```

## 使用方法

### 统一运行入口
```bash
# 处理单个视频
python run_app.py single "YouTube视频URL"

# 批量处理频道 (支持Rhino Finance等财经频道)
python run_app.py batch --limit 20

# 生成分析汇总报告
python run_app.py analyze

# 启动Web仪表板
python -m web.web_dashboard --port 8080
```

### Docker命令
```bash
# 构建镜像
./docker-run.sh build

# 处理视频
./docker-run.sh process "视频URL"

# 交互式应用
./docker-run.sh app

# Jupyter开发环境
./docker-run.sh jupyter

# 进入容器shell  
./docker-run.sh shell
```

## 输出结果

处理完成后，结果保存在 `downloads/YYYY-MM-DD/` 目录：

```
downloads/2025-01-15/
├── audio/           # 音频文件
├── transcription/   # 转录文本  
└── analysis/        # AI分析结果(JSON)
```

### AI分析提取内容
- **市场概况**: 指数表现、成交量、技术分析
- **宏观数据**: 经济指标、央行政策、地缘事件
- **个股分析**: 价格点位、支撑阻力、投资建议
- **风险警示**: 市场风险、个股风险识别

## 项目结构

```
Youtube-Finance-AI/
├── core/                    # 核心功能模块
│   ├── asr_service.py      # 语音识别
│   ├── gemini_llm.py       # Gemini LLM接口
│   ├── info_extractor.py   # 财经信息提取
│   └── youtube_downloader.py # YouTube下载
├── tools/                   # 工具脚本
├── web/                     # Web展示模块  
├── config/                  # 配置文件
├── prompts/                 # Prompt模板
└── downloads/               # 下载结果(按日期组织)
```

## 配置说明

### 依赖安装
```bash
# 基本依赖
uv sync

# 语音转录
uv sync --extra whisper  

# AI分析
uv sync --extra gemini

# 完整安装 (推荐)
uv sync --extra whisper --extra gemini
```

### Whisper模型选择
- **tiny**: 39MB, 最快, 测试用
- **base**: 74MB, 推荐默认 
- **large**: 1550MB, 最高质量

## 注意事项

- ⚠️ 确保 `config/gemini_config.json` 不要提交到Git
- 🔐 定期轮换API密钥
- 📝 视频需要公开可访问
- 💻 首次运行会下载Whisper模型
- 🌐 某些地区可能需要代理访问YouTube

## 许可证

本项目采用 MIT 许可证。

## 致谢

- [OpenAI Whisper](https://github.com/openai/whisper) - 语音识别
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - YouTube下载  
- [Google Gemini](https://ai.google.dev/) - 智能分析

---

⭐ 如果这个项目对你有帮助，请给个Star支持一下！
