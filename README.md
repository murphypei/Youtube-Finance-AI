# YouTube Finance AI

🎵 基于AI的YouTube财经视频分析工具，支持音频下载、语音转录和智能信息提取。

## 🌟 功能特性

- **🎬 YouTube音频下载**: 支持高质量音频提取，多种格式输出
- **🎤 语音转录**: 基于OpenAI Whisper的高精度中英文语音识别
- **🤖 智能分析**: 使用Google Gemini LLM提取关键财经信息
- **📅 按日期组织**: 自动按日期归档所有结果文件
- **🐳 Docker化部署**: 开箱即用的Docker环境
- **⚡ 一键处理**: 通过简单命令完成整个分析流程

## 📁 项目结构

```
Youtube-Finance-AI/
├── src/                          # 源代码
│   ├── app.py                   # 主程序入口
│   ├── youtube_downloader.py    # YouTube下载器
│   ├── asr_service.py          # 语音识别服务
│   ├── info_extractor.py       # 信息提取器
│   └── gemini_llm.py           # Gemini LLM接口
├── prompts/                     # Prompt模板
│   └── financial_extraction_prompt.txt
├── config/                      # 配置文件
│   ├── gemini_config.json.template
│   └── gemini_config.json      # (需要配置)
├── downloads/                   # 下载结果 (按日期组织)
│   └── YYYY-MM-DD/
│       ├── audio/              # 音频文件
│       ├── transcription/      # 转录文本
│       └── analysis/           # 分析结果
├── docker-run.sh               # Docker运行脚本
├── Dockerfile
└── README.md
```

## 🚀 快速开始

### 前置要求

- Docker
- Docker Compose
- NVIDIA GPU (可选，用于加速)

### 1. 克隆项目

```bash
git clone <repository-url>
cd Youtube-Finance-AI
```

### 2. 配置Gemini LLM (可选)

如果要使用智能分析功能，需要配置Google Gemini：

```bash
cp config/gemini_config.json.template config/gemini_config.json
# 编辑config/gemini_config.json，填入你的Google Cloud凭据
```

详细配置说明请参考 [config/README.md](config/README.md)

### 3. 构建Docker镜像

```bash
./docker-run.sh build
```

### 4. 处理YouTube视频

#### 方式一：使用预设链接 (推荐)

编辑 `docker-run.sh` 中的 `default_url` 变量，设置你的YouTube链接：

```bash
# 编辑docker-run.sh，修改quick函数中的default_url
local default_url="https://www.youtube.com/watch?v=你的视频ID"
```

然后运行：

```bash
./docker-run.sh quick
```

#### 方式二：指定链接处理

```bash
./docker-run.sh process "https://www.youtube.com/watch?v=视频ID"
```

#### 方式三：带选项处理

```bash
./docker-run.sh process "https://www.youtube.com/watch?v=视频ID" --filename "my_video" --model large --format mp3
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

AI提取的关键信息包括：

- **市场概况**: 主要指数表现、点位、涨跌幅
- **宏观数据**: 经济指标实际值vs预期值
- **个股分析**: 股价、财报数据、技术点位
- **投资建议**: 具体操作建议和理由
- **风险提示**: 详细风险因素分析

## 🛠 高级用法

### 命令行选项

```bash
python src/app.py --help

选项:
  --filename TEXT        输出文件名
  --format [webm|mp3|m4a|wav]  音频格式 (默认: webm)
  --model [tiny|base|small|medium|large]  Whisper模型 (默认: base)
  --language [auto|zh|en|zh-en]  语言设置 (默认: auto)
  --no-date-folder      不使用日期文件夹组织
  --output-dir TEXT     自定义输出目录
```

### Docker命令

```bash
# 构建镜像
./docker-run.sh build

# 处理视频（推荐）
./docker-run.sh quick --model large

# 指定链接处理
./docker-run.sh process "https://youtube.com/watch?v=ID"

# 交互式应用
./docker-run.sh app

# 进入容器shell
./docker-run.sh shell

# 清理资源
./docker-run.sh clean

# 查看帮助
./docker-run.sh help
```

## 🔧 配置说明

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

- YouTube视频需要公开可访问
- 某些地区可能需要代理
- Gemini API有调用次数限制
- 长视频处理需要更多时间和资源

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