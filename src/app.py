"""
YouTube音频下载和转录主程序
整合youtube_downloader和asr_service功能
"""

import sys
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# 添加当前目录到Python路径，以便导入模块
current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from youtube_downloader import YouTubeDownloader
from asr_service import WhisperASR, WHISPER_AVAILABLE
from info_extractor import FinancialInfoExtractor


def download_and_transcribe_youtube(
    youtube_url: str,
    output_dir: Optional[str] = None,
    filename: Optional[str] = None,
    audio_format: str = 'webm',
    model_size: str = "base",
    language: str = "auto",
    use_date_folder: bool = True,
    **whisper_kwargs
) -> Dict[str, Any]:
    """
    下载YouTube音频并使用ASR服务转录为文本
    
    Args:
        youtube_url: YouTube视频链接
        output_dir: 输出目录，默认为当前目录的downloads文件夹
        filename: 输出文件名（不含扩展名），为None时使用默认命名
        audio_format: 音频格式，推荐'webm'
        model_size: Whisper模型大小 ("tiny", "base", "small", "medium", "large")
        language: 语言设置 ("auto", "zh", "en", "zh-en")
        **whisper_kwargs: Whisper的额外参数
        
    Returns:
        包含下载和转录结果的字典
    """
    print(f"🎬 开始处理YouTube视频: {youtube_url}")
    
    # 检查ASR服务是否可用
    if not WHISPER_AVAILABLE:
        return {
            'success': False,
            'error': 'Whisper ASR不可用。请运行: uv sync 安装依赖',
            'url': youtube_url
        }
    
    # 步骤1: 设置按日期组织的下载目录
    if use_date_folder:
        today = datetime.now().strftime("%Y-%m-%d")
        if output_dir:
            date_output_dir = Path(output_dir) / today
        else:
            date_output_dir = Path.cwd() / "downloads" / today
        date_output_dir.mkdir(parents=True, exist_ok=True)
        final_output_dir = str(date_output_dir)
    else:
        final_output_dir = output_dir
    
    # 初始化YouTube下载器
    downloader = YouTubeDownloader(final_output_dir)
    print(f"📁 下载目录: {downloader.download_dir}")
    
    if use_date_folder:
        print(f"📅 按日期组织: {today}")
        # 创建子目录
        subdirs = ['video', 'audio', 'transcription', 'analysis']
        for subdir in subdirs:
            (date_output_dir / subdir).mkdir(exist_ok=True)
    
    # 步骤2: 下载音频
    print("📥 开始下载音频...")
    download_result = downloader.download_audio(youtube_url, filename, audio_format)
    
    if not download_result['success']:
        return {
            'success': False,
            'error': f"音频下载失败: {download_result.get('error', '未知错误')}",
            'url': youtube_url,
            'download_result': download_result
        }
    
    print(f"✅ 音频下载成功: {download_result['title']}")
    
    # 步骤3: 查找下载的音频文件
    audio_files = list(downloader.download_dir.glob(f"{filename or '*'}.*"))
    audio_file = None
    
    for file in audio_files:
        if file.suffix.lower() in ['.webm', '.mp3', '.m4a', '.wav', '.flac']:
            audio_file = file
            break
    
    if audio_file is None:
        return {
            'success': False,
            'error': '找不到下载的音频文件',
            'url': youtube_url,
            'download_result': download_result
        }
    
    print(f"📄 找到音频文件: {audio_file}")
    
    # 步骤4: 初始化ASR服务并转录
    print("🎤 开始语音转录...")
    asr_service = WhisperASR()
    transcription_result = asr_service.transcribe_audio(
        str(audio_file), model_size, language, **whisper_kwargs
    )
    
    if not transcription_result['success']:
        return {
            'success': False,
            'error': f"转录失败: {transcription_result.get('error', '未知错误')}",
            'url': youtube_url,
            'download_result': download_result,
            'transcription_result': transcription_result,
            'audio_file': str(audio_file)
        }
    
    print(f"✅ 转录成功！")
    
    # 步骤5: 保存转录结果到文本文件
    if use_date_folder:
        # 将音频文件移动到audio子目录
        audio_subdir = date_output_dir / "audio"
        new_audio_path = audio_subdir / audio_file.name
        if audio_file != new_audio_path:
            audio_file.rename(new_audio_path)
            audio_file = new_audio_path
        
        # 转录文件保存到transcription子目录
        transcription_subdir = date_output_dir / "transcription"
        text_file = transcription_subdir / f"{audio_file.stem}.txt"
    else:
        text_file = audio_file.with_suffix('.txt')
    
    try:
        with open(text_file, 'w', encoding='utf-8') as f:
            f.write(transcription_result['text'])
        print(f"💾 转录文本已保存到: {text_file}")
        transcription_result['text_file'] = str(text_file)
    except Exception as e:
        print(f"⚠️ 保存转录文本失败: {e}")
    
    # 步骤6: 提取关键财经信息
    print("🤖 开始提取关键财经信息...")
    extractor = FinancialInfoExtractor()
    key_info = extractor.extract_key_info(
        transcription_text=transcription_result['text'],
        video_title=download_result.get('title', '未知')
    )
    
    # 保存提取信息到JSON文件
    if use_date_folder:
        analysis_subdir = date_output_dir / "analysis"
        info_file = analysis_subdir / f"{audio_file.stem}_analysis.json"
    else:
        info_file = audio_file.with_suffix('.json')
    
    extractor.save_extracted_info(key_info, str(info_file))
    
    # 步骤7: 打印转录内容和关键信息
    print("\n" + "="*50)
    print("📝 转录内容:")
    print("="*50)
    print(transcription_result['text'])
    print("="*50)
    
    # 打印关键信息摘要
    print("\n" + "="*50)
    print("📊 关键信息摘要:")
    print("="*50)
    
    if key_info.get('summary'):
        print(f"📋 内容概要: {key_info['summary']}")
    
    if key_info.get('stock_analysis'):
        print("\n📈 个股分析:")
        for stock in key_info['stock_analysis']:
            print(f"  🏢 {stock.get('symbol', 'N/A')}: {stock.get('company_name', 'N/A')}")
            if stock.get('key_points'):
                for point in stock['key_points'][:2]:  # 显示前2个要点
                    print(f"    • {point}")
    
    if key_info.get('macroeconomic_data'):
        print("\n🌍 宏观数据:")
        for data in key_info['macroeconomic_data'][:3]:  # 显示前3个
            print(f"  📊 {data.get('indicator', 'N/A')}: {data.get('value', 'N/A')}")
    
    if key_info.get('investment_advice'):
        print("\n💡 投资建议:")
        for advice in key_info['investment_advice'][:3]:  # 显示前3个
            print(f"  • {advice}")
    
    print("="*50)
    print(f"💾 详细分析已保存至: {info_file}")
    
    # 返回综合结果
    return {
        'success': True,
        'title': download_result.get('title', '未知'),
        'duration': download_result.get('duration', 0),
        'url': youtube_url,
        'audio_file': str(audio_file),
        'text': transcription_result.get('text', ''),
        'text_file': transcription_result.get('text_file', ''),
        'language': transcription_result.get('language', 'unknown'),
        'language_display': transcription_result.get('language_display', '未知'),
        'model_size': model_size,
        'service': 'whisper',
        'download_result': download_result,
        'transcription_result': transcription_result,
        'key_info': key_info,
        'info_file': str(info_file),
        'message': f"成功下载、转录并分析: {download_result.get('title', '未知')}"
    }


def main():
    """主函数，处理命令行参数或交互式输入"""
    parser = argparse.ArgumentParser(
        description="🎵 YouTube音频下载和转录工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python app.py "https://www.youtube.com/watch?v=XXXXX"
  python app.py --url "https://www.youtube.com/watch?v=XXXXX" --filename "finance_video"
  python app.py --url "https://www.youtube.com/watch?v=XXXXX" --model large --no-date-folder
        """
    )
    
    parser.add_argument(
        'url', nargs='?',
        help='YouTube视频链接'
    )
    parser.add_argument(
        '--url', 
        help='YouTube视频链接 (可选，与位置参数二选一)'
    )
    parser.add_argument(
        '--filename', 
        help='输出文件名 (不含扩展名，默认自动生成)'
    )
    parser.add_argument(
        '--format', 
        choices=['webm', 'mp3', 'm4a', 'wav'], 
        default='webm',
        help='音频格式 (默认: webm)'
    )
    parser.add_argument(
        '--model', 
        choices=['tiny', 'base', 'small', 'medium', 'large'], 
        default='base',
        help='Whisper模型大小 (默认: base)'
    )
    parser.add_argument(
        '--language', 
        choices=['auto', 'zh', 'en', 'zh-en'], 
        default='auto',
        help='语言设置 (默认: auto)'
    )
    parser.add_argument(
        '--no-date-folder', 
        action='store_true',
        help='不使用日期文件夹组织文件'
    )
    parser.add_argument(
        '--output-dir', 
        help='输出目录 (默认: ./downloads)'
    )
    
    args = parser.parse_args()
    
    print("🎵 YouTube音频下载和转录工具")
    print("-" * 40)
    
    # 检查ASR服务状态
    if not WHISPER_AVAILABLE:
        print("❌ Whisper ASR不可用")
        print("💡 请运行以下命令安装依赖:")
        print("   uv sync")
        return
    
    # 获取YouTube链接
    youtube_url = args.url
    if not youtube_url:
        youtube_url = input("🔗 请输入YouTube视频链接: ").strip()
    
    if not youtube_url:
        print("❌ 请提供有效的YouTube链接")
        parser.print_help()
        return
    
    print(f"🔗 处理链接: {youtube_url}")
    print(f"📝 文件名: {args.filename or '自动生成'}")
    print(f"🎵 音频格式: {args.format}")
    print(f"🧠 模型大小: {args.model}")
    print(f"🌐 语言设置: {args.language}")
    print(f"📁 按日期组织: {'否' if args.no_date_folder else '是'}")
    
    print("\n🚀 开始处理...")
    
    # 执行下载和转录
    result = download_and_transcribe_youtube(
        youtube_url=youtube_url,
        output_dir=args.output_dir,
        filename=args.filename,
        audio_format=args.format,
        model_size=args.model,
        language=args.language,
        use_date_folder=not args.no_date_folder
    )
    
    # 显示结果
    print("\n" + "="*50)
    print("📊 处理结果:")
    print("="*50)
    
    if result['success']:
        print(f"✅ 处理成功!")
        print(f"📺 视频标题: {result['title']}")
        print(f"⏱️ 视频时长: {result['duration']} 秒")
        print(f"🌐 检测语言: {result['language_display']} ({result['language']})")
        print(f"🧠 使用模型: {result['model_size']}")
        print(f"📄 音频文件: {result['audio_file']}")
        print(f"💾 文本文件: {result.get('text_file', '未保存')}")
        print(f"📊 分析文件: {result.get('info_file', '未保存')}")
        print(f"📝 文本长度: {len(result['text'])} 字符")
        
        # 显示提取的关键信息摘要
        if result.get('key_info'):
            key_info = result['key_info']
            extraction_method = key_info.get('extraction_method', 'unknown')
            
            print(f"\n🤖 信息提取方法: {extraction_method}")
            
            if key_info.get('summary'):
                print(f"📋 内容摘要: {key_info['summary']}")
            
            # 显示股票数量
            stocks = key_info.get('stock_analysis', [])
            if stocks:
                stock_symbols = [s.get('symbol', 'N/A') for s in stocks]
                print(f"📈 分析股票: {', '.join(stock_symbols)}")
            
            # 显示宏观数据数量
            macro_data = key_info.get('macroeconomic_data', [])
            if macro_data:
                print(f"🌍 宏观数据: {len(macro_data)}条")
            
            # 显示投资建议数量
            advice = key_info.get('investment_advice', [])
            if advice:
                print(f"💡 投资建议: {len(advice)}条")
    else:
        print(f"❌ 处理失败: {result['error']}")


if __name__ == "__main__":
    main()
