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


# 运行交互式shell
shell() {
    echo -e "${BLUE}💻 启动交互式Shell...${NC}"
    check_gpu
    docker-compose run --rm youtube-finance-ai bash
}

# 运行app.py交互式应用
app() {
    echo -e "${BLUE}📱 启动交互式应用...${NC}"
    check_gpu
    docker-compose run --rm youtube-finance-ai python src/app.py
}


# 运行Python命令
python() {
    echo -e "${BLUE}🐍 运行Python命令...${NC}"
    check_gpu
    docker-compose run --rm youtube-finance-ai python "$@"
}


# 启动Jupyter服务
jupyter() {
    echo -e "${BLUE}📓 启动Jupyter Notebook...${NC}"
    echo -e "${YELLOW}访问地址: http://localhost:8888${NC}"
    check_gpu
    docker-compose --profile jupyter up jupyter
}

# 处理指定YouTube视频
process() {
    if [ -z "$1" ]; then
        echo -e "${YELLOW}📖 使用方法: $0 process <YouTube_URL> [options]${NC}"
        echo -e "${YELLOW}示例:${NC}"
        echo -e "${YELLOW}  $0 process 'https://www.youtube.com/watch?v=X-WKPmeeGLM'${NC}"
        echo -e "${YELLOW}  $0 process 'https://www.youtube.com/watch?v=X-WKPmeeGLM' --filename 'finance_video'${NC}"
        echo -e "${YELLOW}  $0 process 'https://www.youtube.com/watch?v=X-WKPmeeGLM' --model large --audio-format wav${NC}"
        return 1
    fi
    
    local url="$1"
    shift  # 移除第一个参数，剩下的作为选项传递
    
    echo -e "${BLUE}🎬 处理YouTube视频...${NC}"
    echo -e "${YELLOW}URL: $url${NC}"
    
    check_gpu
    docker-compose run --rm youtube-finance-ai python src/app.py "$url" "$@"
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
    echo "  $0 app                - 启动交互式应用（app.py）"
    echo "  $0 shell              - 启动交互式Shell"
    echo "  $0 python <args>      - 运行Python命令"
    echo ""
    echo -e "${YELLOW}YouTube处理:${NC}"
    echo "  $0 process <url>      - 处理指定的YouTube视频"
    echo ""
    echo -e "${YELLOW}开发工具:${NC}"
    echo "  $0 jupyter            - 启动Jupyter Notebook"
    echo ""
    echo -e "${YELLOW}维护命令:${NC}"
    echo "  $0 clean              - 清理Docker资源"
    echo "  $0 help               - 显示此帮助信息"
    echo ""
    echo -e "${YELLOW}示例:${NC}"
    echo "  $0 build                                      - 构建镜像"
    echo "  $0 process 'https://www.youtube.com/watch?v=X-WKPmeeGLM'"
    echo "  $0 process 'https://www.youtube.com/watch?v=X-WKPmeeGLM' --filename 'finance_video'"
    echo "  $0 process 'https://www.youtube.com/watch?v=X-WKPmeeGLM' --model large --video-format mp4"
    echo "  $0 app                                        - 启动交互式应用"
}

# 主命令处理
case "${1:-help}" in
    build)
        build
        ;;
    run)
        run
        ;;
    app)
        app
        ;;
    process)
        shift
        process "$@"
        ;;
    shell)
        shell
        ;;
    python)
        shift
        python "$@"
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
