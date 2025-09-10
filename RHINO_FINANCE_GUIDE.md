# 🦏 Rhino Finance 频道批量分析指南

这是一个完整的Rhino Finance频道视频批量分析和展示系统，包含视频下载、分析和Web仪表板展示功能。

## 🌟 功能特色

- **📺 批量视频处理**: 自动获取频道最新20个视频并进行分析
- **🤖 智能分析**: 使用Gemini LLM提取财经关键信息  
- **📊 数据汇总**: 按日期聚合分析结果，提取宏观新闻和股票点位
- **🌐 Web仪表板**: 美观的网页界面展示分析结果
- **📈 股票追踪**: 智能识别买入/卖出/持有建议和支撑阻力位

## 🚀 快速开始

### 1. 安装依赖

```bash
# 安装Flask (用于Web仪表板)
pip install flask

# 确保已安装项目依赖
uv sync --extra whisper --extra gemini
```

### 2. 批量处理Rhino Finance频道视频

```bash
# 处理最新20个视频 (推荐配置)
python src/rhino_finance.py --limit 20 --audio-format webm --model base

# 如果需要同时下载视频文件
python src/rhino_finance.py --limit 20 --audio-format webm --video-format mp4 --model large

# 只处理最新10个视频 (测试用)
python src/rhino_finance.py --limit 10
```

### 3. 生成分析汇总报告

```bash
# 生成汇总报告 (最新1天宏观新闻 + 最近7天股票点位)
python src/analyzer.py

# 自定义提取天数
python src/analyzer.py --macro-days 2 --stock-days 14
```

### 4. 启动Web仪表板

```bash
# 创建网站模板 (首次运行)
python src/web_dashboard.py --create-templates

# 启动Web服务
python src/web_dashboard.py

# 自定义端口和调试模式
python src/web_dashboard.py --port 8080 --debug
```

然后在浏览器访问: http://localhost:5000

## 📁 文件结构

处理完成后，文件将按以下结构组织：

```
downloads/rhino_finance/
├── YYYY-MM-DD/                    # 按日期分组
│   ├── video/                     # 视频文件 (如果下载)
│   ├── audio/                     # 音频文件
│   ├── transcription/             # 转录文本
│   └── analysis/                  # AI分析结果 (JSON)
├── batch_results_YYYYMMDD_HHMMSS.json  # 批量处理结果
├── summary_report_YYYYMMDD_HHMMSS.json # 汇总分析报告
└── templates/                     # 网站模板
    └── dashboard.html
```

## 📊 Web仪表板功能

### 统计概览
- 📰 宏观新闻数量
- 📈 股票分析数量  
- ⬆️ 买入建议数量
- ⬇️ 卖出建议数量

### 宏观新闻展示
- 最新一天的重要宏观经济数据
- 经济指标实际值vs预期值
- 重要市场事件和政策变化

### 股票点位表格
- 📈 **股票代码和公司名称**
- 💰 **当前价格** 
- 🎯 **操作建议**: 买入/卖出/持有/观望
- 📉 **支撑位**: 关键支撑价格点位
- 📈 **阻力位**: 关键阻力价格点位
- 📅 **分析日期**: 数据更新时间

## 🔧 高级配置

### 命令行参数

#### rhino_finance.py
```bash
--channel TEXT          YouTube频道URL (默认: @RhinoFinance)
--limit INTEGER          处理视频数量 (默认: 20)
--audio-format [webm|mp3|m4a|wav]  音频格式 (默认: webm)
--video-format [none|mp4|webm|mkv] 视频格式 (默认: none)
--model [tiny|base|small|medium|large] Whisper模型 (默认: base)
```

#### analyzer.py
```bash
--data-dir TEXT          数据目录路径
--macro-days INTEGER     宏观新闻提取天数 (默认: 1)
--stock-days INTEGER     股票点位提取天数 (默认: 7)
```

#### web_dashboard.py
```bash
--data-dir TEXT          数据目录路径
--host TEXT              服务器地址 (默认: 0.0.0.0)
--port INTEGER           端口号 (默认: 5000)
--debug                  启用调试模式
```

## 📈 分析结果示例

### 宏观新闻格式
```json
{
  "date": "2025-01-15",
  "indicator": "CPI同比",
  "value": "2.1%",
  "expected": "2.0%",
  "impact": "通胀预期升温",
  "description": "12月CPI同比上涨2.1%，略高于预期"
}
```

### 股票点位格式
```json
{
  "symbol": "NVDA",
  "company_name": "NVIDIA Corporation", 
  "current_price": "$124.50",
  "action": "买入",
  "support_levels": ["$120", "$115"],
  "resistance_levels": ["$130", "$135"],
  "outlook": "看好AI芯片需求增长，建议逢低买入"
}
```

## 🚨 注意事项

### 运行环境要求
- **Python 3.8+**
- **yt-dlp**: 视频下载
- **OpenAI Whisper**: 语音转录
- **Google Gemini API**: 智能分析 (需配置API密钥)
- **Flask**: Web仪表板

### 使用限制
- 频道视频需要公开可访问
- Gemini API调用有次数限制
- 大模型处理需要更多时间和资源
- 建议分批处理，避免一次处理过多视频

### 推荐配置
- **快速测试**: `--limit 5 --model base`
- **标准配置**: `--limit 20 --model base --audio-format webm`  
- **高质量配置**: `--limit 20 --model large --audio-format wav`

## 🎯 完整工作流程

1. **批量下载和分析**:
   ```bash
   python src/rhino_finance.py --limit 20 --model base
   ```

2. **生成汇总报告**:
   ```bash
   python src/analyzer.py
   ```

3. **启动Web展示**:
   ```bash
   python src/web_dashboard.py
   ```

4. **浏览器访问**: http://localhost:5000

## 🔄 自动化运行

可以创建定时任务，每日自动更新分析结果：

```bash
# 添加到crontab，每天早上8点运行
0 8 * * * cd /path/to/Youtube-Finance-AI && python src/rhino_finance.py --limit 5 && python src/analyzer.py
```

## 🆘 常见问题

### Q: 视频下载失败怎么办？
A: 检查网络连接和视频可访问性，某些地区可能需要代理

### Q: Gemini分析失败怎么办？  
A: 检查API配置和网络，或使用基础规则提取模式

### Q: Web页面空白怎么办？
A: 确保已运行分析器生成数据，检查浏览器控制台错误信息

### Q: 如何更改分析的频道？
A: 使用 `--channel` 参数指定其他YouTube频道URL

---

🎉 **开始使用Rhino Finance分析系统，让AI为你的投资决策提供智能支持！**
