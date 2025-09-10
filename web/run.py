"""
Web模块独立运行脚本
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="运行Web模块")
    parser.add_argument('service', choices=['dashboard', 'analyze'], help='选择要运行的服务')
    args, remaining = parser.parse_known_args()
    
    # 重置sys.argv
    sys.argv = [f"web/{args.service}.py"] + remaining
    
    if args.service == 'dashboard':
        from web.web_dashboard import main
        main()
    elif args.service == 'analyze':
        from web.analyzer import main
        main()
