#!/usr/bin/env python3
"""
Docker环境下的完整功能测试
"""

import sys
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from youtube_downloader import download_and_transcribe_youtube


def main():
    """测试Docker环境下的完整功能"""
    print("🎬 Docker环境下的YouTube转录测试")
    print("=" * 50)
    
    test_url = "https://www.youtube.com/watch?v=X-WKPmeeGLM"
    filename = "docker_test"
    
    print(f"📹 测试URL: {test_url}")
    print(f"📁 输出文件名: {filename}")
    print(f"🧠 使用模型: base")
    print(f"🌐 语言检测: auto (中英文混杂)")
    print()
    
    try:
        print("🚀 开始下载和转录...")
        result = download_and_transcribe_youtube(
            url=test_url,
            filename=filename,
            model_size="base",
            language="auto"
        )
        
        print("\n" + "=" * 50)
        print("📊 处理结果:")
        print("=" * 50)
        
        if result['success']:
            print(f"✅ 状态: 成功")
            print(f"📺 标题: {result['title']}")
            print(f"⏱️  时长: {result['duration']} 秒")
            print(f"🌐 检测语言: {result['language_display']}")
            print(f"🧠 使用模型: {result['model_size']}")
            print(f"📝 文本长度: {len(result['text'])} 个字符")
            print(f"💾 音频文件: {result['audio_file']}")
            print(f"📄 文本文件: {result.get('text_file', '未生成')}")
            
            if result['text']:
                print(f"\n📖 转录文本预览 (前200字符):")
                print("-" * 40)
                print(result['text'][:200])
                print("-" * 40)
            
        else:
            print(f"❌ 状态: 失败")
            print(f"🔍 错误信息: {result.get('error', '未知错误')}")
            
            # 显示详细的错误信息
            if 'download_result' in result:
                download_result = result['download_result']
                print(f"📥 下载结果: {download_result}")
                
            if 'transcription_result' in result:
                trans_result = result['transcription_result']
                print(f"🎤 转录结果: {trans_result}")
    
    except Exception as e:
        print(f"\n❌ 程序执行出错: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\n🏁 测试完成")


if __name__ == "__main__":
    main()
