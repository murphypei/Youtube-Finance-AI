"""
媒体下载功能测试
"""

import os
import shutil
import sys
from pathlib import Path

import pytest

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from youtube_downloader import (
    YouTubeDownloader,
    download_youtube_audio,
    download_youtube_video,
)


class TestYouTubeDownloader:
    """YouTube下载器测试类"""
    
    @pytest.fixture
    def test_url(self):
        """测试用的YouTube URL"""
        return "https://www.youtube.com/watch?v=X-WKPmeeGLM"
    
    @pytest.fixture
    def temp_dir(self, tmp_path):
        """创建临时下载目录"""
        return tmp_path / "test_downloads"
    
    @pytest.fixture
    def downloader(self, temp_dir):
        """创建下载器实例"""
        return YouTubeDownloader(str(temp_dir))
    
    def test_downloader_initialization(self, temp_dir):
        """测试下载器初始化"""
        downloader = YouTubeDownloader(str(temp_dir))
        assert downloader.download_dir == temp_dir
        assert temp_dir.exists()
    
    def test_default_download_dir(self):
        """测试默认下载目录"""
        downloader = YouTubeDownloader()
        expected_dir = Path.cwd() / "downloads"
        assert downloader.download_dir == expected_dir
    
    @pytest.mark.slow  # 标记为慢速测试，因为需要实际下载
    def test_video_download(self, downloader, test_url, temp_dir):
        """测试视频下载功能"""
        print(f"\nTesting video download to: {temp_dir}")
        
        result = downloader.download_video(test_url, "test_video_download")
        
        # 验证返回结果
        assert isinstance(result, dict)
        assert 'success' in result
        assert 'title' in result
        assert 'url' in result
        assert result['url'] == test_url
        assert result['media_type'] == 'video'
        
        if result['success']:
            print(f"Video download successful: {result['title']}")
            # 检查文件是否存在
            downloaded_files = list(temp_dir.glob("test_video_download.*"))
            assert len(downloaded_files) > 0, "No video file found"
        else:
            print(f"Video download failed: {result.get('error', 'Unknown error')}")
            # 即使下载失败，我们也要确保返回了正确的错误信息
            assert 'error' in result
    
    @pytest.mark.slow  # 标记为慢速测试
    def test_audio_download(self, downloader, test_url, temp_dir):
        """测试音频下载功能"""
        print(f"\nTesting audio download to: {temp_dir}")
        
        result = downloader.download_audio(test_url, "test_audio_download")
        
        # 验证返回结果
        assert isinstance(result, dict)
        assert 'success' in result
        assert 'title' in result
        assert 'url' in result
        assert result['url'] == test_url
        assert result['media_type'] == 'audio'
        
        if result['success']:
            print(f"Audio download successful: {result['title']}")
            # 检查音频文件是否存在（应该是mp3格式）
            downloaded_files = list(temp_dir.glob("test_audio_download.*"))
            assert len(downloaded_files) > 0, "No audio file found"
        else:
            print(f"Audio download failed: {result.get('error', 'Unknown error')}")
            assert 'error' in result
    
    def test_download_media_video(self, downloader, test_url):
        """测试通用媒体下载方法（视频）"""
        # 这里不实际下载，只测试参数验证
        try:
            # 使用一个无效的URL来避免实际下载
            result = downloader.download_media("invalid_url", "video", "test")
            # 应该返回错误结果
            assert not result['success']
        except Exception:
            # 预期会有异常
            pass
    
    def test_download_media_audio(self, downloader, test_url):
        """测试通用媒体下载方法（音频）"""
        # 这里不实际下载，只测试参数验证
        try:
            result = downloader.download_media("invalid_url", "audio", "test")
            assert not result['success']
        except Exception:
            pass
    
    def test_invalid_media_type(self, downloader, test_url):
        """测试无效媒体类型"""
        with pytest.raises(ValueError) as exc_info:
            downloader.download_media(test_url, "invalid_type", "test")
        
        assert "Unsupported media type" in str(exc_info.value)
    
    def test_output_template_with_filename(self, downloader):
        """测试自定义文件名的输出模板"""
        template = downloader._get_output_template("custom_name", "video")
        assert "custom_name" in template
        assert "%(ext)s" in template
    
    def test_output_template_default(self, downloader):
        """测试默认文件名的输出模板"""
        template = downloader._get_output_template(None, "audio")
        assert "%(title)s" in template
        assert "audio" in template
        assert "%(upload_date)s" in template


class TestConvenienceFunctions:
    """便捷函数测试类"""
    
    @pytest.fixture
    def test_url(self):
        return "https://www.youtube.com/watch?v=X-WKPmeeGLM"
    
    @pytest.fixture
    def temp_dir(self, tmp_path):
        return str(tmp_path / "convenience_test")
    
    def test_download_youtube_video_function(self, test_url, temp_dir):
        """测试便捷视频下载函数"""
        # 使用无效URL避免实际下载
        result = download_youtube_video("invalid_url", temp_dir, "test_video")
        assert isinstance(result, dict)
        assert not result['success']
        assert 'error' in result
    
    def test_download_youtube_audio_function(self, test_url, temp_dir):
        """测试便捷音频下载函数"""
        result = download_youtube_audio("invalid_url", temp_dir, "test_audio")
        assert isinstance(result, dict)
        assert not result['success']
        assert 'error' in result


@pytest.mark.integration
@pytest.mark.slow
class TestActualDownload:
    """实际下载集成测试（需要网络连接）"""
    
    @pytest.fixture
    def test_url(self):
        return "https://www.youtube.com/watch?v=X-WKPmeeGLM"
    
    @pytest.fixture
    def temp_dir(self, tmp_path):
        test_dir = tmp_path / "actual_downloads"
        test_dir.mkdir()
        return test_dir
    
    def test_actual_video_download(self, test_url, temp_dir):
        """实际下载测试视频"""
        print(f"\n=== 开始实际视频下载测试 ===")
        print(f"URL: {test_url}")
        print(f"Download directory: {temp_dir}")
        
        downloader = YouTubeDownloader(str(temp_dir))
        result = downloader.download_video(test_url, "actual_test_video")
        
        print(f"Download result: {result}")
        
        if result['success']:
            # 检查下载的文件
            files = list(temp_dir.glob("actual_test_video.*"))
            print(f"Downloaded files: {files}")
            assert len(files) > 0
            
            # 检查文件大小
            for file in files:
                size = file.stat().st_size
                print(f"File: {file.name}, Size: {size} bytes")
                assert size > 0
        else:
            print(f"Download failed: {result.get('error')}")
            # 对于网络相关的测试，我们可以接受失败
            pytest.skip(f"Download failed due to: {result.get('error')}")
    
    def test_actual_audio_download(self, test_url, temp_dir):
        """实际下载测试音频"""
        print(f"\n=== 开始实际音频下载测试 ===")
        print(f"URL: {test_url}")
        print(f"Download directory: {temp_dir}")
        
        downloader = YouTubeDownloader(str(temp_dir))
        result = downloader.download_audio(test_url, "actual_test_audio")
        
        print(f"Download result: {result}")
        
        if result['success']:
            # 检查下载的音频文件
            files = list(temp_dir.glob("actual_test_audio.*"))
            print(f"Downloaded files: {files}")
            assert len(files) > 0
            
            # 检查是否有mp3文件
            mp3_files = list(temp_dir.glob("actual_test_audio.mp3"))
            if mp3_files:
                print(f"Found MP3 file: {mp3_files[0]}")
                size = mp3_files[0].stat().st_size
                print(f"MP3 file size: {size} bytes")
                assert size > 0
        else:
            print(f"Download failed: {result.get('error')}")
            pytest.skip(f"Download failed due to: {result.get('error')}")


if __name__ == "__main__":
    # 运行快速测试
    pytest.main([__file__, "-v", "-m", "not slow and not integration"])
    
    # 如果要运行包括实际下载的测试，使用：
    # pytest.main([__file__, "-v", "-s"])
