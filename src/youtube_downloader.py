"""
YouTube媒体下载模块
使用yt-dlp库下载YouTube视频和音频
"""

import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import yt_dlp

# 导入Whisper ASR服务
try:
    from .asr_service import WhisperASR
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    print("⚠️ Whisper ASR不可用。请运行: uv sync 安装依赖")


class YouTubeDownloader:
    """YouTube下载器类"""

    def __init__(self, download_dir: Optional[str] = None):
        """
        初始化下载器

        Args:
            download_dir: 下载目录，默认为当前目录的downloads文件夹
        """
        if download_dir is None:
            self.download_dir = Path.cwd() / "downloads"
        else:
            self.download_dir = Path(download_dir)

        # 确保下载目录存在
        self.download_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化Whisper ASR服务
        self.whisper_asr = WhisperASR() if WHISPER_AVAILABLE else None

    def download_video(self, url: str, output_filename: Optional[str] = None) -> Dict[str, Any]:
        """
        下载视频

        Args:
            url: YouTube视频URL
            output_filename: 输出文件名（不包括扩展名），为None时使用默认命名

        Returns:
            Dict包含下载结果信息
        """
        print(f"Starting video download from: {url}")

        # 配置yt-dlp选项
        ydl_opts = {
            "outtmpl": self._get_output_template(output_filename, "video"),
            "format": "best[ext=mp4]/best",  # 优先下载mp4格式的最佳质量视频
        }

        return self._download_with_ytdlp(url, ydl_opts, "video")

    def download_audio(
        self, url: str, output_filename: Optional[str] = None, audio_format: str = "webm"
    ) -> Dict[str, Any]:
        """
        下载音频（从视频中提取）

        Args:
            url: YouTube视频URL
            output_filename: 输出文件名（不包括扩展名），为None时使用默认命名
            audio_format: 音频格式，支持 'mp3', 'webm', 'm4a', 'wav' 等

        Returns:
            Dict包含下载结果信息
        """
        print(f"Starting audio download from: {url}")

        # 配置yt-dlp选项用于提取音频
        ydl_opts = {
            "outtmpl": self._get_output_template(output_filename, "audio"),
            "format": "bestaudio/best",  # 下载最佳音质
        }

        # 如果请求mp3格式，尝试转换；如果转换失败则保持原格式
        if audio_format.lower() == "mp3":
            ydl_opts["postprocessors"] = [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            ]
            print("Attempting MP3 conversion (requires FFmpeg with libmp3lame)")
        elif audio_format.lower() in ["m4a", "wav", "flac"]:
            ydl_opts["postprocessors"] = [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": audio_format.lower(),
                    "preferredquality": "192" if audio_format.lower() != "wav" else None,
                }
            ]
            print(f"Attempting {audio_format.upper()} conversion (requires FFmpeg)")
        else:
            print(f"Using original audio format (typically WebM/OGG)")

        return self._download_with_ytdlp(url, ydl_opts, "audio")
    
    def download_and_transcribe(self, url: str, output_filename: Optional[str] = None,
                               audio_format: str = 'webm', model_size: str = "base",
                               language: str = "auto", **whisper_kwargs) -> Dict[str, Any]:
        """
        下载音频并进行Whisper语音识别转录
        
        Args:
            url: YouTube视频URL
            output_filename: 输出文件名（不包括扩展名）
            audio_format: 音频格式，推荐'webm'
            model_size: Whisper模型大小 ("tiny", "base", "small", "medium", "large")
            language: 语言设置 ("auto", "zh", "en", "zh-en")
            **whisper_kwargs: Whisper的额外参数
            
        Returns:
            Dict包含下载和转录结果
        """
        if not WHISPER_AVAILABLE or self.whisper_asr is None:
            return {
                'success': False,
                'error': 'Whisper ASR不可用。请运行: uv sync 安装依赖',
                'url': url,
                'download_result': {},
                'transcription_result': {}
            }
        
        print(f"Starting download and transcription from: {url}")
        
        # 第一步：下载音频
        download_result = self.download_audio(url, output_filename, audio_format)
        
        if not download_result['success']:
            return {
                'success': False,
                'error': f"Audio download failed: {download_result.get('error', 'Unknown error')}",
                'url': url,
                'download_result': download_result,
                'transcription_result': {}
            }
        
        # 第二步：找到下载的音频文件
        audio_files = list(self.download_dir.glob(f"{output_filename or '*'}.*"))
        audio_file = None
        
        for file in audio_files:
            if file.suffix.lower() in ['.webm', '.mp3', '.m4a', '.wav', '.flac']:
                audio_file = file
                break
        
        if audio_file is None:
            return {
                'success': False,
                'error': 'Downloaded audio file not found',
                'url': url,
                'download_result': download_result,
                'transcription_result': {}
            }
        
        print(f"Found audio file: {audio_file}")
        
        # 第三步：使用Whisper进行语音识别
        transcription_result = self.whisper_asr.transcribe_audio(
            str(audio_file), model_size, language, **whisper_kwargs
        )
        
        # 第四步：保存转录结果到文本文件
        if transcription_result['success'] and transcription_result['text']:
            text_file = audio_file.with_suffix('.txt')
            try:
                with open(text_file, 'w', encoding='utf-8') as f:
                    f.write(transcription_result['text'])
                print(f"Transcription saved to: {text_file}")
                transcription_result['text_file'] = str(text_file)
            except Exception as e:
                print(f"Warning: Failed to save transcription to file: {e}")
        
        # 返回综合结果
        return {
            'success': transcription_result['success'],
            'title': download_result.get('title', 'Unknown'),
            'duration': download_result.get('duration', 0),
            'url': url,
            'audio_file': str(audio_file),
            'text': transcription_result.get('text', ''),
            'text_file': transcription_result.get('text_file', ''),
            'language': transcription_result.get('language', 'unknown'),
            'language_display': transcription_result.get('language_display', '未知'),
            'model_size': model_size,
            'service': 'whisper',
            'download_result': download_result,
            'transcription_result': transcription_result,
            'message': f"成功下载并转录: {download_result.get('title', 'Unknown')}"
        }

    def download_media(
        self, url: str, media_type: str = "video", output_filename: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        通用媒体下载方法

        Args:
            url: YouTube视频URL
            media_type: 媒体类型，'video' 或 'audio'
            output_filename: 输出文件名（不包括扩展名）

        Returns:
            Dict包含下载结果信息
        """
        if media_type.lower() == "video":
            return self.download_video(url, output_filename)
        elif media_type.lower() == "audio":
            return self.download_audio(url, output_filename)
        else:
            raise ValueError(f"Unsupported media type: {media_type}. Use 'video' or 'audio'.")

    def _get_output_template(self, filename: Optional[str], media_type: str) -> str:
        """
        获取输出文件模板

        Args:
            filename: 用户指定的文件名
            media_type: 媒体类型

        Returns:
            yt-dlp输出模板字符串
        """
        if filename:
            # 用户指定了文件名，使用指定的文件名
            return str(self.download_dir / f"{filename}.%(ext)s")
        else:
            # 使用默认命名：标题_类型_日期
            return str(self.download_dir / f"%(title)s_{media_type}_%(upload_date)s.%(ext)s")

    def _download_with_ytdlp(self, url: str, ydl_opts: Dict, media_type: str) -> Dict[str, Any]:
        """
        使用yt-dlp执行下载

        Args:
            url: 视频URL
            ydl_opts: yt-dlp选项
            media_type: 媒体类型

        Returns:
            下载结果字典
        """
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # 获取视频信息
                info = ydl.extract_info(url, download=False)
                title = info.get("title", "Unknown")
                duration = info.get("duration", 0)

                print(f"Found {media_type}: {title}")
                print(f"Duration: {duration} seconds")

                # 执行下载
                ydl.download([url])

                return {
                    "success": True,
                    "title": title,
                    "duration": duration,
                    "url": url,
                    "media_type": media_type,
                    "download_dir": str(self.download_dir),
                    "message": f"Successfully downloaded {media_type}: {title}",
                }

        except Exception as e:
            error_msg = f"Error downloading {media_type} from {url}: {str(e)}"
            print(error_msg)
            return {"success": False, "error": str(e), "url": url, "media_type": media_type, "message": error_msg}


# 便捷函数
def download_youtube_video(
    url: str, output_dir: Optional[str] = None, filename: Optional[str] = None
) -> Dict[str, Any]:
    """
    便捷函数：下载YouTube视频

    Args:
        url: YouTube视频URL
        output_dir: 输出目录
        filename: 文件名（不含扩展名）

    Returns:
        下载结果字典
    """
    downloader = YouTubeDownloader(output_dir)
    return downloader.download_video(url, filename)


def download_youtube_audio(
    url: str, output_dir: Optional[str] = None, filename: Optional[str] = None, audio_format: str = "webm"
) -> Dict[str, Any]:
    """
    便捷函数：下载YouTube音频

    Args:
        url: YouTube视频URL
        output_dir: 输出目录
        filename: 文件名（不含扩展名）
        audio_format: 音频格式，支持 'mp3', 'webm', 'm4a', 'wav' 等

    Returns:
        下载结果字典
    """
    downloader = YouTubeDownloader(output_dir)
    return downloader.download_audio(url, filename, audio_format)


def download_youtube_media(
    url: str, media_type: str = "video", output_dir: Optional[str] = None, filename: Optional[str] = None
) -> Dict[str, Any]:
    """
    便捷函数：下载YouTube媒体

    Args:
        url: YouTube视频URL
        media_type: 媒体类型，'video' 或 'audio'
        output_dir: 输出目录
        filename: 文件名（不含扩展名）

    Returns:
        下载结果字典
    """
    downloader = YouTubeDownloader(output_dir)
    return downloader.download_media(url, media_type, filename)


def download_and_transcribe_youtube(url: str, output_dir: Optional[str] = None,
                                   filename: Optional[str] = None,
                                   audio_format: str = 'webm',
                                   model_size: str = "base",
                                   language: str = "auto",
                                   **whisper_kwargs) -> Dict[str, Any]:
    """
    便捷函数：下载YouTube音频并使用Whisper进行转录
    
    Args:
        url: YouTube视频URL
        output_dir: 输出目录
        filename: 文件名（不含扩展名）
        audio_format: 音频格式，推荐'webm'
        model_size: Whisper模型大小 ("tiny", "base", "small", "medium", "large")
        language: 语言设置 ("auto", "zh", "en", "zh-en")
        **whisper_kwargs: Whisper的额外参数
        
    Returns:
        下载和转录结果字典
    """
    downloader = YouTubeDownloader(output_dir)
    return downloader.download_and_transcribe(
        url, filename, audio_format, model_size, language, **whisper_kwargs
    )


if __name__ == "__main__":
    # 示例使用
    test_url = "https://www.youtube.com/watch?v=X-WKPmeeGLM"

    # 测试视频下载
    print("=== 测试视频下载 ===")
    result = download_youtube_video(test_url, filename="test_video")
    print(f"Video download result: {result}")

    # 测试音频下载
    print("\n=== 测试音频下载 ===")
    result = download_youtube_audio(test_url, filename="test_audio")
    print(f"Audio download result: {result}")
    
    # 测试下载并转录功能
    print("\n=== 测试Whisper下载转录功能 ===")
    if WHISPER_AVAILABLE:
        print("🎤 Whisper ASR可用，开始测试...")
        result = download_and_transcribe_youtube(
            test_url, 
            filename="test_whisper_transcribe",
            audio_format="webm",
            model_size="base",
            language="auto"
        )
        print(f"Whisper转录结果:")
        print(f"  ✅ 成功: {result.get('success', False)}")
        print(f"  📺 标题: {result.get('title', 'Unknown')}")
        print(f"  🌐 检测语言: {result.get('language_display', 'unknown')}")
        print(f"  🧠 模型: {result.get('model_size', 'unknown')}")
        print(f"  📝 文本长度: {len(result.get('text', ''))}")
        print(f"  📄 文本文件: {result.get('text_file', 'None')}")
        if result.get('text'):
            print(f"  📖 文本预览: {result['text'][:200]}...")
            
        if not result.get('success'):
            print(f"  ❌ 错误: {result.get('error', 'Unknown error')}")
    else:
        print("⚠️ Whisper ASR不可用。请运行: uv sync")
        
        # 显示Whisper服务信息
        downloader = YouTubeDownloader()
        if downloader.whisper_asr:
            info = downloader.whisper_asr.get_model_info()
            print(f"Whisper服务信息: {info}")
        else:
            print("💡 安装Whisper后可享受:")
            print("  - 完全免费的本地语音识别")  
            print("  - 优秀的中英文混杂识别效果")
            print("  - 多种模型大小选择")
    
    print("\n=== 测试完成 ===")
