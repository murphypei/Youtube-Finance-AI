#!/bin/bash
# YouTube Finance AI Docker 运行脚本

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🐳 YouTube Finance AI Docker 管理脚本${NC}"

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker未安装，请先安装Docker${NC}"
    exit 1
fi

# 检查Docker Compose是否安装
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo -e "${RED}❌ Docker Compose未安装，请先安装Docker Compose${NC}"
    exit 1
fi

# 检查NVIDIA Docker支持
check_gpu() {
    if command -v nvidia-smi &> /dev/null; then
        echo -e "${GREEN}✅ 检测到NVIDIA GPU${NC}"
        nvidia-smi --query-gpu=name,memory.total,memory.used --format=csv,noheader,nounits
    else
        echo -e "${YELLOW}⚠️ 未检测到NVIDIA GPU或nvidia-smi命令${NC}"
    fi
}

# 构建Docker镜像
build() {
    echo -e "${BLUE}📦 构建Docker镜像...${NC}"
    docker-compose build --no-cache
    echo -e "${GREEN}✅ 镜像构建完成${NC}"
}

# 运行主应用
run() {
    echo -e "${BLUE}🚀 启动YouTube Finance AI应用...${NC}"
    check_gpu
    docker-compose up youtube-finance-ai
}

# 运行交互式shell
shell() {
    echo -e "${BLUE}💻 启动交互式Shell...${NC}"
    check_gpu
    docker-compose run --rm youtube-finance-ai bash
}

# 运行Python命令
python() {
    echo -e "${BLUE}🐍 运行Python命令...${NC}"
    check_gpu
    docker-compose run --rm youtube-finance-ai python "$@"
}

# 测试Whisper功能
test_whisper() {
    echo -e "${BLUE}🎤 测试Whisper ASR功能...${NC}"
    check_gpu
    docker-compose run --rm youtube-finance-ai python -m src.asr_service
}

# 下载并转录YouTube视频
transcribe() {
    if [ -z "$1" ]; then
        echo -e "${YELLOW}📖 使用方法: $0 transcribe <YouTube_URL> [filename]${NC}"
        echo -e "${YELLOW}示例: $0 transcribe 'https://www.youtube.com/watch?v=X-WKPmeeGLM' 'finance_video'${NC}"
        return 1
    fi
    
    local url="$1"
    local filename="${2:-youtube_transcribe}"
    
    echo -e "${BLUE}🎬 下载并转录YouTube视频...${NC}"
    echo -e "${YELLOW}URL: $url${NC}"
    echo -e "${YELLOW}文件名: $filename${NC}"
    
    check_gpu
    docker-compose run --rm youtube-finance-ai python -c "
from src.youtube_downloader import download_and_transcribe_youtube
import sys

url = '$url'
filename = '$filename'

print(f'🎯 开始处理: {url}')
result = download_and_transcribe_youtube(
    url,
    filename=filename,
    model_size='base',
    language='auto'
)

if result['success']:
    print(f'✅ 成功完成!')
    print(f'📺 标题: {result[\"title\"]}')
    print(f'🌐 语言: {result[\"language_display\"]}')
    print(f'📝 文本长度: {len(result[\"text\"])}')
    print(f'📄 文本文件: {result[\"text_file\"]}')
    if result['text']:
        print(f'📖 文本预览: {result[\"text\"][:200]}...')
else:
    print(f'❌ 处理失败: {result.get(\"error\", \"Unknown error\")}')
    sys.exit(1)
"
}

# 启动Jupyter服务
jupyter() {
    echo -e "${BLUE}📓 启动Jupyter Notebook...${NC}"
    echo -e "${YELLOW}访问地址: http://localhost:8888${NC}"
    check_gpu
    docker-compose --profile jupyter up jupyter
}

# 清理Docker资源
clean() {
    echo -e "${BLUE}🧹 清理Docker资源...${NC}"
    docker-compose down --volumes --remove-orphans
    docker system prune -f
    echo -e "${GREEN}✅ 清理完成${NC}"
}

# 显示帮助信息
help() {
    echo -e "${BLUE}📖 YouTube Finance AI Docker 使用指南${NC}"
    echo ""
    echo -e "${YELLOW}基本命令:${NC}"
    echo "  $0 build              - 构建Docker镜像"
    echo "  $0 run                - 运行主应用"
    echo "  $0 shell              - 启动交互式Shell"
    echo "  $0 python <args>      - 运行Python命令"
    echo ""
    echo -e "${YELLOW}ASR功能:${NC}"
    echo "  $0 test-whisper       - 测试Whisper功能"
    echo "  $0 transcribe <url> [name] - 下载并转录YouTube视频"
    echo ""
    echo -e "${YELLOW}开发工具:${NC}"
    echo "  $0 jupyter            - 启动Jupyter Notebook"
    echo ""
    echo -e "${YELLOW}维护命令:${NC}"
    echo "  $0 clean              - 清理Docker资源"
    echo "  $0 help               - 显示此帮助信息"
    echo ""
    echo -e "${YELLOW}示例:${NC}"
    echo "  $0 transcribe 'https://www.youtube.com/watch?v=X-WKPmeeGLM' 'finance_video'"
}

# 主命令处理
case "${1:-help}" in
    build)
        build
        ;;
    run)
        run
        ;;
    shell)
        shell
        ;;
    python)
        shift
        python "$@"
        ;;
    test-whisper)
        test_whisper
        ;;
    transcribe)
        shift
        transcribe "$@"
        ;;
    jupyter)
        jupyter
        ;;
    clean)
        clean
        ;;
    help|--help|-h)
        help
        ;;
    *)
        echo -e "${RED}❌ 未知命令: $1${NC}"
        echo ""
        help
        exit 1
        ;;
esac
