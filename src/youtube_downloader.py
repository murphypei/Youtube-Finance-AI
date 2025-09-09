"""
YouTube媒体下载模块
使用yt-dlp库下载YouTube视频和音频
"""

from pathlib import Path
from typing import Any, Dict, Optional

import yt_dlp



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
    
    
    print("\n=== 测试完成 ===")
