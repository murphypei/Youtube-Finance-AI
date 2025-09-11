"""
Rhino Finance 频道批量处理脚本
自动获取频道最新视频并进行批量分析
"""

import sys
import os
import json
import subprocess
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse, parse_qs

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from scripts.single_video import download_and_transcribe_youtube

class RhinoFinanceProcessor:
    """Rhino Finance 频道处理器"""
    
    def __init__(self, channel_url: str = "https://www.youtube.com/@RhinoFinance"):
        """
        初始化处理器
        
        Args:
            channel_url: 频道URL
        """
        self.channel_url = channel_url
        self.output_dir = Path.cwd() / "downloads" / "rhino_finance"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"🦏 初始化 Rhino Finance 处理器")
        print(f"📺 频道: {channel_url}")
        print(f"📁 输出目录: {self.output_dir}")
    
    def get_channel_videos(self, limit: int = 20) -> List[str]:
        """
        获取频道最新的视频URL列表
        
        Args:
            limit: 获取视频数量限制
            
        Returns:
            视频URL列表（从最新到最旧排序）
        """
        print(f"🔍 获取频道最新 {limit} 个视频...")
        
        try:
            # 使用yt-dlp获取频道视频列表
            cmd = [
                "yt-dlp", 
                "--flat-playlist", 
                "--print", "url",
                "--playlist-end", str(limit),  # 限制获取数量
                self.channel_url
            ]
            
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                check=True
            )
            
            # 解析输出，每行一个URL
            video_urls = [url.strip() for url in result.stdout.split('\n') if url.strip()]
            
            print(f"✅ 成功获取 {len(video_urls)} 个视频URL")
            for i, url in enumerate(video_urls[:5], 1):
                print(f"   {i}. {url}")
            if len(video_urls) > 5:
                print(f"   ... 等 {len(video_urls)} 个视频")
                
            return video_urls
            
        except subprocess.CalledProcessError as e:
            print(f"❌ 获取视频列表失败: {e}")
            print(f"错误输出: {e.stderr}")
            return []
        except Exception as e:
            print(f"❌ 获取视频列表时发生异常: {e}")
            return []
    
    def extract_video_id(self, url: str) -> Optional[str]:
        """从YouTube URL中提取视频ID"""
        try:
            parsed = urlparse(url)
            if 'youtube.com' in parsed.netloc:
                if 'watch' in parsed.path:
                    return parse_qs(parsed.query).get('v', [None])[0]
                elif 'embed' in parsed.path:
                    return parsed.path.split('/')[-1]
            elif 'youtu.be' in parsed.netloc:
                return parsed.path[1:]
            return None
        except Exception:
            return None
    
    def process_videos(
        self, 
        video_urls: List[str], 
        audio_format: str = "webm",
        video_format: str = "none",
        model_size: str = "base"
    ) -> List[Dict[str, Any]]:
        """
        批量处理视频列表
        
        Args:
            video_urls: 视频URL列表
            audio_format: 音频格式
            video_format: 视频格式
            model_size: Whisper模型大小
            
        Returns:
            处理结果列表
        """
        print(f"\n🚀 开始批量处理 {len(video_urls)} 个视频...")
        print(f"🎵 音频格式: {audio_format}")
        print(f"🎬 视频格式: {video_format}")
        print(f"🧠 模型大小: {model_size}")
        
        results = []
        
        for i, url in enumerate(video_urls, 1):
            print(f"\n{'='*60}")
            print(f"🎬 处理第 {i}/{len(video_urls)} 个视频")
            print(f"🔗 URL: {url}")
            print(f"{'='*60}")
            
            try:
                # 为每个视频生成唯一的文件名
                video_id = self.extract_video_id(url)
                filename = f"rhino_{video_id}" if video_id else f"rhino_video_{i:03d}"
                
                # 调用现有的处理函数
                result = download_and_transcribe_youtube(
                    youtube_url=url,
                    output_dir=str(self.output_dir),
                    filename=filename,
                    audio_format=audio_format,
                    video_format=video_format,
                    model_size=model_size,
                    language="auto",
                    use_date_folder=True
                )
                
                # 添加处理时间和序号
                result['processed_at'] = datetime.now().isoformat()
                result['video_index'] = i
                result['video_id'] = video_id
                
                results.append(result)
                
                if result['success']:
                    print(f"✅ 第 {i} 个视频处理成功: {result.get('title', '未知标题')}")
                else:
                    print(f"❌ 第 {i} 个视频处理失败: {result.get('error', '未知错误')}")
                    
            except Exception as e:
                print(f"❌ 处理第 {i} 个视频时发生异常: {e}")
                results.append({
                    'success': False,
                    'error': str(e),
                    'url': url,
                    'video_index': i,
                    'processed_at': datetime.now().isoformat()
                })
            
            # 添加短暂延迟，避免请求过快
            import time
            time.sleep(2)
        
        print(f"\n🎉 批量处理完成!")
        success_count = sum(1 for r in results if r.get('success', False))
        print(f"✅ 成功: {success_count}/{len(results)}")
        print(f"❌ 失败: {len(results) - success_count}/{len(results)}")
        
        return results
    
    def save_batch_results(self, results: List[Dict[str, Any]]) -> str:
        """
        保存批量处理结果
        
        Args:
            results: 处理结果列表
            
        Returns:
            保存的文件路径
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = self.output_dir / f"batch_results_{timestamp}.json"
        
        # 创建汇总信息
        summary = {
            'processed_at': datetime.now().isoformat(),
            'total_videos': len(results),
            'successful_videos': sum(1 for r in results if r.get('success', False)),
            'failed_videos': sum(1 for r in results if not r.get('success', False)),
            'results': results
        }
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        print(f"💾 批量处理结果已保存: {results_file}")
        return str(results_file)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="🦏 Rhino Finance 频道批量处理工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python rhino_finance.py --limit 10
  python rhino_finance.py --limit 20 --audio-format wav --model large
  python rhino_finance.py --limit 5 --video-format mp4
        """
    )
    
    parser.add_argument(
        '--channel',
        default="https://www.youtube.com/@RhinoFinance",
        help='YouTube频道URL (默认: RhinoFinance)'
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=20,
        help='处理视频数量限制 (默认: 20)'
    )
    parser.add_argument(
        '--audio-format',
        choices=['webm', 'mp3', 'm4a', 'wav'],
        default='wav',
        help='音频格式 (默认: wav)'
    )
    parser.add_argument(
        '--video-format',
        choices=['none', 'mp4', 'webm', 'mkv'],
        default='mp4',
        help='视频格式 (默认: mp4)'
    )
    parser.add_argument(
        '--model',
        choices=['tiny', 'base', 'small', 'medium', 'large'],
        default='large',
        help='Whisper模型大小 (默认: large)'
    )
    
    args = parser.parse_args()
    
    print("🦏 Rhino Finance 频道批量处理工具")
    print("=" * 50)
    print(f"📺 频道: {args.channel}")
    print(f"📊 处理数量: {args.limit}")
    print(f"🎵 音频格式: {args.audio_format}")
    print(f"🎬 视频格式: {args.video_format}")
    print(f"🧠 模型大小: {args.model}")
    
    # 初始化处理器
    processor = RhinoFinanceProcessor(args.channel)
    
    # 获取视频列表
    video_urls = processor.get_channel_videos(args.limit)
    if not video_urls:
        print("❌ 未获取到视频，退出程序")
        return
    
    # 批量处理视频
    results = processor.process_videos(
        video_urls=video_urls,
        audio_format=args.audio_format,
        video_format=args.video_format,
        model_size=args.model
    )
    
    # 保存结果
    results_file = processor.save_batch_results(results)
    
    print(f"\n🎊 全部处理完成!")
    print(f"📄 结果文件: {results_file}")


if __name__ == "__main__":
    main()
