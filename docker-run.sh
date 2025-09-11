#!/bin/bash
# YouTube Finance AI Docker 管理脚本 (简化版)

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🐳 YouTube Finance AI Docker 管理脚本${NC}"

# 检查Docker是否安装
if ! command -v docker &>/dev/null; then
    echo -e "${RED}❌ Docker未安装，请先安装Docker${NC}"
    exit 1
fi

# 检查Docker Compose是否安装
if ! command -v docker-compose &>/dev/null && ! docker compose version &>/dev/null; then
    echo -e "${RED}❌ Docker Compose未安装，请先安装Docker Compose${NC}"
    exit 1
fi

# 检查NVIDIA Docker支持
check_gpu() {
    if command -v nvidia-smi &>/dev/null; then
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

# 运行交互式shell
shell() {
    echo -e "${BLUE}💻 启动交互式Shell...${NC}"
    check_gpu
    docker-compose run --rm youtube-finance-ai bash
}

# 启动Jupyter服务
jupyter() {
    echo -e "${BLUE}📓 启动Jupyter Notebook...${NC}"
    echo -e "${YELLOW}访问地址: http://localhost:8850${NC}"
    check_gpu
    docker-compose --profile jupyter up jupyter
}

# 启动交互式shell（用于运行web服务）
web() {
    echo -e "${BLUE}🌐 启动交互式Shell（用于Web服务）...${NC}"
    echo -e "${YELLOW}进入Shell后运行: python -m web.web_dashboard${NC}"
    echo -e "${YELLOW}访问地址: http://localhost:5000${NC}"
    check_gpu
    docker-compose run --rm --service-ports youtube-finance-ai bash
}

# 停止所有服务
stop() {
    echo -e "${BLUE}🛑 停止所有Docker服务...${NC}"
    docker-compose down
    echo -e "${GREEN}✅ 所有服务已停止${NC}"
}

# 显示帮助信息
help() {
    echo -e "${BLUE}📖 YouTube Finance AI Docker 使用指南${NC}"
    echo ""
    echo -e "${YELLOW}基本命令:${NC}"
    echo "  $0 build              - 构建Docker镜像"
    echo "  $0 shell              - 启动交互式Shell"
    echo "  $0 web                - 启动交互式Shell (用于Web服务)"
    echo "  $0 jupyter            - 启动Jupyter Notebook"
    echo "  $0 stop               - 停止所有Docker服务"
    echo "  $0 help               - 显示此帮助信息"
    echo ""
    echo -e "${YELLOW}脚本使用:${NC}"
    echo -e "${YELLOW}在Shell中直接运行Python脚本:${NC}"
    echo ""
    echo "  # 处理单个视频"
    echo "  python scripts/single_video.py 'https://www.youtube.com/watch?v=XXX' --audio-format wav"
    echo ""
    echo "  # 批量处理频道"
    echo "  python scripts/batch_channel.py --channel '@RhinoFinance' --limit 20"
    echo ""
    echo "  # 重新处理转录文件"
    echo "  python scripts/reprocess_transcripts.py --force"
    echo ""
    echo -e "${YELLOW}或在本地使用Docker Compose:${NC}"
    echo ""
    echo "  docker-compose run --rm youtube-finance-ai python scripts/single_video.py 'URL'"
    echo "  docker-compose run --rm youtube-finance-ai python scripts/batch_channel.py --limit 20"
    echo "  docker-compose run --rm youtube-finance-ai python scripts/reprocess_transcripts.py --force"
}

# 主命令处理
case "${1:-help}" in
build)
    build
    ;;
shell)
    shell
    ;;
web)
    web
    ;;
jupyter)
    jupyter
    ;;
stop)
    stop
    ;;
help | --help | -h)
    help
    ;;
*)
    echo -e "${RED}❌ 未知命令: $1${NC}"
    echo ""
    help
    exit 1
    ;;
esac
