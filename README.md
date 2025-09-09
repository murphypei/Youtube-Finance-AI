# YouTube Finance AI

🎵 基于AI的YouTube财经视频分析工具，集成OpenAI Whisper语音转录和Google Gemini LLM智能分析，一键提取关键投资信息。

## 🌟 功能特性

- **🎬 YouTube媒体下载**: 支持高质量音频/视频提取，多种格式输出
- **🎤 语音转录**: 基于OpenAI Whisper的高精度中英文语音识别
- **🤖 AI财经分析**: 使用Google Gemini LLM深度提取关键投资信息
- **📊 智能信息提取**: 自动识别股票代码、价格点位、市场数据和投资建议
- **📅 按日期组织**: 自动按日期归档所有结果文件
- **🐳 Docker化部署**: 开箱即用的Docker环境，支持GPU加速
- **💻 开发环境**: 集成Jupyter Notebook，便于交互式开发和调试
- **⚡ 一键处理**: 通过简单命令完成整个分析流程
- **📦 现代包管理**: 基于pyproject.toml的依赖管理，支持可选组件

## 📁 项目结构

```
Youtube-Finance-AI/
├── src/                          # 源代码
│   ├── app.py                   # 主程序入口
│   ├── youtube_downloader.py    # YouTube下载器
│   ├── asr_service.py          # 语音识别服务
│   ├── info_extractor.py       # 财经信息提取器
│   └── gemini_llm.py           # Gemini LLM接口
├── prompts/                     # Prompt模板
│   └── financial_extraction_prompt.txt
├── config/                      # 配置文件
│   ├── gemini_config.json.template
│   ├── gemini_config.json      # Gemini API配置 (需要配置)
│   └── README.md               # 配置说明文档
├── downloads/                   # 下载结果 (按日期组织)
│   └── YYYY-MM-DD/
│       ├── video/              # 视频文件 (可选)
│       ├── audio/              # 音频文件
│       ├── transcription/      # 转录文本
│       └── analysis/           # AI分析结果 (JSON格式)
├── pyproject.toml              # 现代Python项目配置
├── docker-compose.yml          # Docker Compose配置 (含GPU支持)
├── docker-run.sh               # Docker运行脚本
├── Dockerfile
└── README.md
```

## 🚀 快速开始

### 前置要求

- **Docker** 和 **Docker Compose**
- **NVIDIA GPU** (可选，用于Whisper加速)
- **Google Cloud API密钥** (可选，用于Gemini LLM分析)
- **Python 3.8+** (如果不使用Docker)

### 1. 克隆项目

```bash
git clone <repository-url>
cd Youtube-Finance-AI
```

### 2. 安装依赖 (非Docker方式，不推荐)

```bash
# 使用uv (推荐，更快的包管理器)
uv sync --extra whisper --extra gemini

# 或使用pip
pip install -e .[whisper,gemini]
```

### 3. 配置Gemini LLM (可选)

如果要使用AI智能分析功能，需要配置Google Gemini：

```bash
cp config/gemini_config.json.template config/gemini_config.json
# 编辑config/gemini_config.json，填入你的Google Cloud凭据
```

详细配置说明请参考 [config/README.md](config/README.md)

### 4. 构建Docker镜像（推荐）

```bash
./docker-run.sh build
```

### 5. 处理YouTube视频

```bash
./docker-run.sh process "https://www.youtube.com/watch?v=视频ID" --filename "my_video" --model large --audio-format wav
```

## 📊 结果输出

处理完成后，结果将保存在 `downloads/YYYY-MM-DD/` 目录中：

```
downloads/2025-01-15/
├── audio/
│   └── 视频标题_audio.webm          # 提取的音频文件
├── transcription/
│   └── 视频标题_audio.txt            # 转录文本
└── analysis/
    └── 视频标题_audio_analysis.json  # AI分析结果
```

### 分析结果示例

基于Google Gemini LLM的智能财经分析可提取：

#### 📈 市场概况分析
- **主要指数表现**: 实时点位、涨跌幅、成交量分析
- **市场情绪**: 多空判断、波动率评估
- **技术面分析**: 关键支撑阻力位、趋势方向

#### 🌍 宏观经济数据
- **经济指标**: 实际值vs预期值对比
- **央行政策**: 利率决议、货币政策影响
- **地缘事件**: 对市场的潜在影响分析

#### 🏢 个股深度分析
```json
{
  "symbol": "NVDA",
  "company_name": "NVIDIA Corporation",
  "current_price": "$124.50",
  "price_levels": {
    "support": ["$120", "$115"],
    "resistance": ["$130", "$135"]
  },
  "outlook": "看好AI芯片需求增长，建议逢低买入",
  "risk_factors": ["地缘政治风险", "行业竞争加剧"]
}
```

#### 💡 智能投资建议
- **具体操作建议**: 买入/卖出/持有的明确指导
- **仓位管理**: 建议配置比例和风险控制
- **时机判断**: 最佳进出场点位分析

#### ⚠️ 风险警示
- **市场风险**: 系统性风险因素识别
- **个股风险**: 特定公司面临的挑战
- **技术风险**: 技术指标预警信号

## 🛠 高级用法

### 命令行选项

```bash
python src/app.py --help

选项:
  --filename TEXT        输出文件名
  --audio-format [webm|mp3|m4a|wav]  音频格式 (默认: webm)
  --video-format [none|mp4|webm|mkv]  视频格式 (默认: none)
  --model [tiny|base|small|medium|large]  Whisper模型 (默认: base)
  --language [auto|zh|en|zh-en]  语言设置 (默认: auto)
  --no-date-folder      不使用日期文件夹组织
  --output-dir TEXT     自定义输出目录
```

### Docker命令

```bash
# 构建镜像
./docker-run.sh build

# 指定链接处理
./docker-run.sh process "https://youtube.com/watch?v=ID"

# 交互式应用
./docker-run.sh app

# Jupyter Notebook开发环境
./docker-run.sh jupyter

# 进入容器shell
./docker-run.sh shell

# 运行Python命令
./docker-run.sh python <args>

# 清理资源
./docker-run.sh clean

# 查看帮助
./docker-run.sh help
```

### 开发环境设置

#### 启动Jupyter Notebook

```bash
# 启动Jupyter服务 (访问 http://localhost:8888)
./docker-run.sh jupyter

# 或使用Docker Compose
docker-compose --profile jupyter up
```

#### GPU支持配置

如果您有NVIDIA GPU，系统会自动检测并启用GPU加速：

```bash
# 检查GPU是否可用
nvidia-smi

# Docker容器会自动配置CUDA环境变量
```

## 🔧 配置说明

### Python依赖管理

项目使用现代的 `pyproject.toml` 配置，支持可选依赖组合：

```bash
# 安装基本依赖 (仅YouTube下载)
uv sync

# 安装Whisper语音识别依赖
uv sync --extra whisper

# 安装Gemini LLM分析依赖  
uv sync --extra gemini

# 安装所有依赖 (推荐)
uv sync --extra whisper --extra gemini

# 或使用pip
pip install -e .[whisper,gemini]
```

### 可选依赖说明

| 依赖组 | 用途 | 包含组件 |
|--------|------|---------|
| **whisper** | 语音转录 | openai-whisper |
| **gemini** | AI分析 | google-genai, google-api-core |
| **dev** | 开发工具 | pytest, pytest-asyncio |

### Whisper模型选择

| 模型 | 大小 | 速度 | 准确率 | 推荐场景 |
|------|------|------|--------|----------|
| tiny | 39MB | 最快 | 较低 | 快速测试 |
| base | 74MB | 快 | 良好 | **推荐默认** |
| small | 244MB | 中等 | 较好 | 一般使用 |
| medium | 769MB | 较慢 | 很好 | 高准确率需求 |
| large | 1550MB | 最慢 | 最佳 | 最高质量要求 |

### 音频格式支持

- **webm**: 原生格式，无损，推荐
- **mp3**: 通用格式，需要FFmpeg
- **m4a**: 高质量，需要FFmpeg  
- **wav**: 无损，文件较大

## 🚨 注意事项

### 安全提示

- ⚠️ **绝对不要**将 `config/gemini_config.json` 提交到Git仓库
- 🔐 定期轮换API密钥
- 📝 查看 `.gitignore` 确保敏感文件被正确忽略

### 使用限制

- **YouTube访问**: 视频需要公开可访问，某些地区可能需要代理
- **API限制**: Gemini API有调用次数和费用限制
- **硬件要求**: 长视频处理需要更多时间和资源
- **GPU内存**: 使用large模型需要>=8GB显存
- **网络要求**: 首次运行会下载Whisper模型(~1.5GB)

## 🤝 贡献指南

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- [OpenAI Whisper](https://github.com/openai/whisper) - 语音识别
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - YouTube下载
- [Google Gemini](https://ai.google.dev/) - 智能分析
- [PyTorch](https://pytorch.org/) - 深度学习框架

## 📞 支持

如有问题或建议，请提交 [Issue](issues) 或通过以下方式联系：

- 📧 Email: your-email@example.com
- 💬 讨论: [Discussions](discussions)

---

⭐ 如果这个项目对你有帮助，请给个Star支持一下！
