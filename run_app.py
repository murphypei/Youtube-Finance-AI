#!/usr/bin/env python3
"""
YouTube Finance AI 主运行入口
支持运行各种工具和服务
"""

import sys
import argparse
from pathlib import Path

def run_single_video():
    """运行单个视频处理"""
    from tools.app import main
    main()

def run_batch_processing():
    """运行批量处理"""
    from tools.rhino_finance import main
    main()

def run_analyzer():
    """运行分析汇总器"""
    from web.analyzer import main
    main()

def run_web_dashboard():
    """运行Web仪表板"""
    from web.web_dashboard import main
    main()

def main():
    parser = argparse.ArgumentParser(
        description="🎵 YouTube Finance AI 主程序",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
可用的命令:
  single      - 处理单个YouTube视频
  batch       - 批量处理Rhino Finance频道视频
  analyze     - 生成分析汇总报告
  web         - 启动Web仪表板

示例:
  python run_app.py single "https://www.youtube.com/watch?v=XXXXX"
  python run_app.py batch --limit 20
  python run_app.py analyze
  python run_app.py web --port 8080
        """
    )
    
    parser.add_argument(
        'command',
        choices=['single', 'batch', 'analyze', 'web'],
        help='要运行的命令'
    )
    
    # 检查是否只是要查看主帮助
    if len(sys.argv) == 2 and sys.argv[1] in ['--help', '-h']:
        parser.print_help()
        return
    
    # 解析已知参数，其余传递给子命令
    args, remaining = parser.parse_known_args()
    
    # 如果没有命令，显示帮助并退出
    if not hasattr(args, 'command') or not args.command:
        parser.print_help()
        return
    
    # 将剩余参数重新添加到sys.argv，让子命令处理
    sys.argv = [f"run_app.py {args.command}"] + remaining
    
    print(f"🚀 运行 {args.command} 模块...")
    print("-" * 50)
    
    if args.command == 'single':
        run_single_video()
    elif args.command == 'batch':
        run_batch_processing()
    elif args.command == 'analyze':
        run_analyzer()
    elif args.command == 'web':
        run_web_dashboard()

if __name__ == "__main__":
    main()
