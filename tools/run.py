"""
工具模块独立运行脚本
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# 修复相对导入问题
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="运行工具模块")
    parser.add_argument('tool', choices=['app', 'rhino'], help='选择要运行的工具')
    args, remaining = parser.parse_known_args()
    
    # 重置sys.argv
    sys.argv = [f"tools/{args.tool}.py"] + remaining
    
    if args.tool == 'app':
        from tools.app import main
        main()
    elif args.tool == 'rhino':
        from tools.rhino_finance import main  
        main()
