#!/usr/bin/env python3
"""
重新处理现有转录文件的脚本
跳过下载和转录步骤，直接对现有转录文件进行信息提取
"""

import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional
import argparse

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from core.info_extractor import FinancialInfoExtractor

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class TranscriptionReprocessor:
    """转录文件重新处理器"""
    
    def __init__(self, base_dir: str = "downloads"):
        """
        初始化重新处理器
        
        Args:
            base_dir: 下载目录的根路径
        """
        self.base_dir = Path(base_dir)
        self.extractor = FinancialInfoExtractor()
        
    def find_transcription_dirs(self) -> List[Path]:
        """
        查找所有包含转录文件的目录
        
        Returns:
            包含转录文件的目录列表
        """
        transcription_dirs = []
        
        # 遍历所有可能的目录结构
        for item in self.base_dir.rglob("transcription"):
            if item.is_dir() and list(item.glob("*.txt")):
                transcription_dirs.append(item)
                
        logger.info(f"📁 找到 {len(transcription_dirs)} 个转录目录")
        for dir_path in transcription_dirs:
            txt_count = len(list(dir_path.glob("*.txt")))
            logger.info(f"  - {dir_path}: {txt_count} 个转录文件")
            
        return transcription_dirs
        
    def process_transcription_dir(self, transcription_dir: Path, force_reprocess: bool = False) -> Dict[str, any]:
        """
        处理单个转录目录中的所有文件
        
        Args:
            transcription_dir: 转录文件目录路径
            force_reprocess: 是否强制重新处理已存在的分析文件
            
        Returns:
            处理结果统计
        """
        logger.info(f"🔍 处理转录目录: {transcription_dir}")
        
        # 获取对应的分析目录
        analysis_dir = transcription_dir.parent / "analysis"
        analysis_dir.mkdir(exist_ok=True)
        
        # 获取所有转录文件
        txt_files = list(transcription_dir.glob("*.txt"))
        logger.info(f"📄 找到 {len(txt_files)} 个转录文件")
        
        results = {
            "total": len(txt_files),
            "processed": 0,
            "skipped": 0,
            "failed": 0,
            "success": 0
        }
        
        for txt_file in txt_files:
            try:
                # 检查对应的分析文件是否已存在
                analysis_file = analysis_dir / f"{txt_file.stem}_analysis.json"
                
                if analysis_file.exists() and not force_reprocess:
                    logger.info(f"⏭️  跳过已存在的分析文件: {analysis_file.name}")
                    results["skipped"] += 1
                    continue
                
                logger.info(f"🔄 处理转录文件: {txt_file.name}")
                
                # 读取转录内容
                with open(txt_file, 'r', encoding='utf-8') as f:
                    transcription_text = f.read().strip()
                
                if not transcription_text:
                    logger.warning(f"⚠️  转录文件为空: {txt_file.name}")
                    results["failed"] += 1
                    continue
                
                # 从文件名提取视频标题（如果可能）
                video_title = self._extract_title_from_filename(txt_file.name)
                
                logger.info(f"📝 开始提取信息，转录文本长度: {len(transcription_text)} 字符")
                
                # 调用信息提取
                extracted_info = self.extractor.extract_key_info(
                    transcription_text=transcription_text,
                    video_title=video_title
                )
                
                # 保存分析结果
                with open(analysis_file, 'w', encoding='utf-8') as f:
                    json.dump(extracted_info, f, ensure_ascii=False, indent=2)
                
                logger.info(f"✅ 成功保存分析结果: {analysis_file.name}")
                logger.info(f"📊 提取方法: {extracted_info.get('extraction_method', 'unknown')}")
                
                if "tokens_used" in extracted_info:
                    logger.info(f"💰 使用tokens: {extracted_info['tokens_used']}")
                    
                if "attempts_used" in extracted_info:
                    logger.info(f"🔄 重试次数: {extracted_info['attempts_used']}")
                
                results["success"] += 1
                results["processed"] += 1
                
            except Exception as e:
                logger.error(f"❌ 处理失败 {txt_file.name}: {e}")
                results["failed"] += 1
                results["processed"] += 1
                
        return results
    
    def _extract_title_from_filename(self, filename: str) -> str:
        """
        从文件名提取可能的视频标题
        
        Args:
            filename: 转录文件名
            
        Returns:
            提取的标题
        """
        # 移除扩展名和前缀
        base_name = filename.replace('.txt', '')
        if base_name.startswith('rhino_'):
            base_name = base_name[6:]  # 移除 'rhino_' 前缀
            
        # 使用视频ID作为标题（如果需要更智能的标题提取，可以后续改进）
        return f"Rhino Finance Video - {base_name}"
    
    def reprocess_all(self, force_reprocess: bool = False, target_dir: Optional[str] = None) -> None:
        """
        重新处理所有转录文件
        
        Args:
            force_reprocess: 是否强制重新处理已存在的分析文件
            target_dir: 指定的目标目录，如果None则处理所有发现的目录
        """
        logger.info("🚀 开始重新处理转录文件...")
        
        if target_dir:
            # 处理指定目录
            target_path = Path(target_dir)
            if not target_path.exists():
                logger.error(f"❌ 指定目录不存在: {target_dir}")
                return
                
            if target_path.name == "transcription":
                dirs_to_process = [target_path]
            else:
                transcription_dir = target_path / "transcription"
                if transcription_dir.exists():
                    dirs_to_process = [transcription_dir]
                else:
                    logger.error(f"❌ 在指定目录中未找到transcription子目录: {target_dir}")
                    return
        else:
            # 查找所有转录目录
            dirs_to_process = self.find_transcription_dirs()
        
        if not dirs_to_process:
            logger.warning("⚠️  未找到任何转录目录")
            return
        
        total_stats = {
            "total": 0,
            "processed": 0,
            "skipped": 0,
            "failed": 0,
            "success": 0
        }
        
        # 处理每个目录
        for transcription_dir in dirs_to_process:
            try:
                stats = self.process_transcription_dir(transcription_dir, force_reprocess)
                
                # 累计统计
                for key in total_stats:
                    total_stats[key] += stats[key]
                    
                logger.info(f"📊 目录处理完成 {transcription_dir}:")
                logger.info(f"   总计: {stats['total']}, 成功: {stats['success']}, "
                          f"跳过: {stats['skipped']}, 失败: {stats['failed']}")
                          
            except Exception as e:
                logger.error(f"❌ 处理目录失败 {transcription_dir}: {e}")
        
        # 输出总体统计
        logger.info("🎉 全部处理完成!")
        logger.info("📊 总体统计:")
        logger.info(f"   总计文件: {total_stats['total']}")
        logger.info(f"   成功处理: {total_stats['success']}")
        logger.info(f"   跳过文件: {total_stats['skipped']}")
        logger.info(f"   处理失败: {total_stats['failed']}")
        
        if total_stats['success'] > 0:
            success_rate = (total_stats['success'] / total_stats['processed']) * 100 if total_stats['processed'] > 0 else 0
            logger.info(f"   成功率: {success_rate:.1f}%")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="🔄 重新处理现有转录文件，跳过下载和转录步骤",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 处理所有发现的转录文件
  python tools/reprocess_transcriptions.py
  
  # 强制重新处理所有文件（包括已存在分析的文件）
  python tools/reprocess_transcriptions.py --force
  
  # 只处理指定目录
  python tools/reprocess_transcriptions.py --dir downloads/rhino_finance/2025-09-10
  
  # 指定基础下载目录
  python tools/reprocess_transcriptions.py --base-dir /path/to/downloads
        """
    )
    
    parser.add_argument(
        '--force', '-f',
        action='store_true',
        help='强制重新处理已存在分析文件的转录'
    )
    
    parser.add_argument(
        '--dir', '-d',
        type=str,
        help='指定要处理的目录路径（可以是包含transcription的父目录）'
    )
    
    parser.add_argument(
        '--base-dir', '-b',
        type=str,
        default='downloads',
        help='基础下载目录路径 (默认: downloads)'
    )
    
    args = parser.parse_args()
    
    try:
        # 创建重新处理器
        reprocessor = TranscriptionReprocessor(base_dir=args.base_dir)
        
        # 开始处理
        reprocessor.reprocess_all(
            force_reprocess=args.force,
            target_dir=args.dir
        )
        
    except KeyboardInterrupt:
        logger.info("🛑 用户中断处理")
    except Exception as e:
        logger.error(f"❌ 处理过程中发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
