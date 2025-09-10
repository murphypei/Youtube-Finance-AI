"""
基于OpenAI Whisper的自动语音识别(ASR)服务
专注于本地Whisper部署，支持中英文混杂语音识别
"""

import logging
import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional

# 抑制一些不必要的警告
warnings.filterwarnings("ignore", category=UserWarning)
logging.getLogger("transformers").setLevel(logging.ERROR)

try:
    import torch
    import whisper
    WHISPER_AVAILABLE = True
    # 检查CUDA是否可用
    CUDA_AVAILABLE = torch.cuda.is_available()
    if CUDA_AVAILABLE:
        print(f"🚀 检测到GPU: {torch.cuda.get_device_name(0)}")
        print(f"💾 GPU内存: {torch.cuda.get_device_properties(0).total_memory // 1024**3}GB")
    else:
        print("💻 使用CPU进行Whisper推理")
except ImportError:
    WHISPER_AVAILABLE = False
    CUDA_AVAILABLE = False
    print("⚠️ Whisper未安装。请运行: uv sync 安装依赖")


class WhisperASR:
    """基于OpenAI Whisper的语音识别服务类"""
    
    def __init__(self):
        """初始化Whisper ASR服务"""
        self.model = None
        self.current_model_size = None
        
    def transcribe_audio(self, audio_path: str, 
                        model_size: str = "base",
                        language: str = "auto",
                        **kwargs) -> Dict[str, Any]:
        """
        使用Whisper转录音频文件为文本
        
        Args:
            audio_path: 音频文件路径
            model_size: 模型大小 ("tiny", "base", "small", "medium", "large")
            language: 语言代码 ("auto", "zh", "en", "zh-en")
            **kwargs: 额外参数
            
        Returns:
            Dict包含转录结果
        """
        if not WHISPER_AVAILABLE:
            return {
                'success': False,
                'error': 'Whisper未安装。请运行: uv sync',
                'text': '',
                'service': 'whisper'
            }
        
        audio_path = Path(audio_path)
        if not audio_path.exists():
            return {
                'success': False,
                'error': f'音频文件不存在: {audio_path}',
                'text': '',
                'service': 'whisper'
            }
        
        print(f"🎤 开始使用Whisper转录音频")
        print(f"📁 音频文件: {audio_path}")
        print(f"🧠 模型大小: {model_size}")
        
        try:
            # 加载或重用Whisper模型
            if self.model is None or self.current_model_size != model_size:
                print(f"📥 加载Whisper模型: {model_size}")
                # 根据GPU可用性选择设备
                device = "cuda" if CUDA_AVAILABLE else "cpu"
                print(f"🖥️ 使用设备: {device}")
                self.model = whisper.load_model(model_size, device=device)
                self.current_model_size = model_size
                print(f"✅ 模型加载完成 ({device})")
            
            # 设置语言参数
            whisper_language = self._get_whisper_language(language)
                
            # 执行转录
            print("🔄 正在转录音频...")
            result = self.model.transcribe(
                str(audio_path),
                language=whisper_language,
                verbose=False,
                **kwargs
            )
            
            text = result["text"].strip()
            detected_language = result.get("language", "unknown")
            segments = result.get("segments", [])
            
            # 语言显示名称映射
            language_names = {
                'zh': '中文',
                'en': '英文', 
                'ja': '日文',
                'ko': '韩文',
                'unknown': '未知'
            }
            
            language_display = language_names.get(detected_language, detected_language)
            
            print(f"✅ 转录完成!")
            print(f"🌐 检测语言: {language_display} ({detected_language})")
            print(f"📝 文本长度: {len(text)} 个字符")
            print(f"⏱️ 分段数量: {len(segments)}")
            
            return {
                'success': True,
                'text': text,
                'language': detected_language,
                'language_display': language_display,
                'service': 'whisper',
                'model_size': model_size,
                'segments': segments,
                'segment_count': len(segments),
                'text_length': len(text),
                'message': f'成功使用Whisper ({model_size}模型) 转录音频'
            }
            
        except Exception as e:
            error_msg = f"Whisper转录失败: {str(e)}"
            print(f"❌ {error_msg}")
            return {
                'success': False,
                'error': error_msg,
                'text': '',
                'service': 'whisper',
                'model_size': model_size
            }
    
    def _get_whisper_language(self, language: str) -> Optional[str]:
        """
        转换语言参数为Whisper格式
        
        Args:
            language: 输入语言设置
            
        Returns:
            Whisper语言代码或None
        """
        if language in ["auto", "zh-en"]:  # 自动检测或中英混杂
            return None
        elif language == "zh":
            return "zh"
        elif language == "en":
            return "en"
        else:
            return None  # 让Whisper自动检测
    
    def get_available_models(self) -> List[str]:
        """
        获取可用的Whisper模型列表
        
        Returns:
            可用模型列表
        """
        if not WHISPER_AVAILABLE:
            return []
        
        return ["tiny", "base", "small", "medium", "large"]
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        获取模型信息
        
        Returns:
            模型信息字典
        """
        models_info = {
            "tiny": {"size": "39MB", "speed": "最快", "accuracy": "较低", "description": "适合快速测试"},
            "base": {"size": "74MB", "speed": "快", "accuracy": "良好", "description": "平衡速度和准确率，推荐"},
            "small": {"size": "244MB", "speed": "中等", "accuracy": "较好", "description": "适合一般使用"},
            "medium": {"size": "769MB", "speed": "较慢", "accuracy": "很好", "description": "高准确率需求"},
            "large": {"size": "1550MB", "speed": "最慢", "accuracy": "最佳", "description": "最高准确率"}
        }
        
        return {
            "whisper_available": WHISPER_AVAILABLE,
            "cuda_available": CUDA_AVAILABLE,
            "current_model": self.current_model_size,
            "available_models": self.get_available_models(),
            "models_info": models_info,
            "supported_languages": ["auto", "zh", "en", "zh-en"],
            "recommended_model": "base",
            "device": "cuda" if CUDA_AVAILABLE else "cpu"
        }


def transcribe_audio_file(audio_path: str, model_size: str = "base", 
                         language: str = "auto", **kwargs) -> Dict[str, Any]:
    """
    便捷函数：使用Whisper转录音频文件
    
    Args:
        audio_path: 音频文件路径
        model_size: 模型大小
        language: 语言设置
        **kwargs: 额外参数
        
    Returns:
        转录结果
    """
    asr = WhisperASR()
    return asr.transcribe_audio(audio_path, model_size, language, **kwargs)


def get_whisper_info() -> Dict[str, Any]:
    """
    获取Whisper服务信息
    
    Returns:
        服务信息
    """
    asr = WhisperASR()
    return asr.get_model_info()


if __name__ == "__main__":
    # 显示Whisper信息
    print("🎤 Whisper ASR 服务信息:")
    info = get_whisper_info()
    
    print(f"✅ Whisper可用: {info['whisper_available']}")
    print(f"🚀 CUDA加速: {info.get('cuda_available', False)}")
    print(f"🖥️ 使用设备: {info.get('device', 'unknown')}")
    print(f"🧠 可用模型: {', '.join(info['available_models'])}")
    print(f"⭐ 推荐模型: {info['recommended_model']}")
    print(f"🌐 支持语言: {', '.join(info['supported_languages'])}")
    
    # 模型详细信息
    print(f"\n📊 模型详细信息:")
    for model, details in info['models_info'].items():
        print(f"  {model}: {details['size']}, {details['speed']}, {details['description']}")
    
    # 如果有测试音频文件，进行转录测试
    test_audio_dir = Path("downloads")
    if test_audio_dir.exists():
        audio_files = list(test_audio_dir.glob("*.webm"))
        if audio_files and info['whisper_available']:
            print(f"\n🧪 测试转录第一个音频文件...")
            test_file = audio_files[0]
            print(f"📁 测试文件: {test_file}")
            
            result = transcribe_audio_file(str(test_file), "base", "auto")
            
            if result['success']:
                print(f"✅ 转录成功!")
                print(f"🌐 检测语言: {result['language_display']}")
                print(f"📝 文本长度: {result['text_length']}")
                print(f"📄 文本预览: {result['text'][:150]}...")
            else:
                print(f"❌ 转录失败: {result['error']}")
        elif not info['whisper_available']:
            print(f"\n⚠️ Whisper未安装，无法进行转录测试")
        else:
            print(f"\n📂 未找到测试音频文件 ({test_audio_dir})")
    
    print(f"\n💡 使用提示:")
    print(f"  - 对于中英文混杂的YouTube视频，推荐使用'auto'语言检测")
    print(f"  - 'base'模型提供最佳的速度和准确率平衡")
    print(f"  - 如需最高准确率，使用'large'模型（但速度较慢）")
