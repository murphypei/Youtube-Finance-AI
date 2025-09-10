"""
财经信息提取器
从ASR转录的文本中提取关键投资信息，包括宏观数据、个股分析、关键点位等
"""

import sys
import json
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path

project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# 设置日志
logger = logging.getLogger(__name__)

# 尝试导入gemini_llm
try:
    from core.gemini_llm import GeminiLLM, gemini_config
    GEMINI_AVAILABLE = True
except ImportError as e:
    GEMINI_AVAILABLE = False
    logger.warning(f"Gemini LLM不可用，请检查依赖和配置: {e}")


class FinancialInfoExtractor:
    """财经信息提取器类"""
    
    def __init__(self, use_gemini: bool = True):
        """
        初始化信息提取器
        
        Args:
            use_gemini: 是否使用Gemini LLM进行提取
        """
        logger.info(f"🔧 初始化信息提取器, use_gemini={use_gemini}, GEMINI_AVAILABLE={GEMINI_AVAILABLE}")
        
        self.use_gemini = use_gemini and GEMINI_AVAILABLE
        self.llm = None
        
        if not GEMINI_AVAILABLE:
            logger.warning("⚠️ Gemini不可用: 模块导入失败")
        elif not use_gemini:
            logger.info("ℹ️ 用户选择不使用Gemini LLM")
        else:
            try:
                logger.info("🚀 尝试初始化Gemini LLM...")
                self.llm = GeminiLLM(gemini_config)
                logger.info("✅ Gemini LLM初始化成功")
            except Exception as e:
                logger.error(f"❌ Gemini LLM初始化失败: {e}")
                import traceback
                traceback.print_exc()
                self.use_gemini = False
    
    def extract_key_info(self, transcription_text: str, video_title: str = "") -> Dict[str, Any]:
        """
        从转录文本中提取关键财经信息
        
        Args:
            transcription_text: ASR转录的文本
            video_title: 视频标题
            
        Returns:
            包含提取信息的字典
        """
        if not self.use_gemini:
            return self._extract_without_llm(transcription_text, video_title)
        
        try:
            logger.info("🤖 开始使用Gemini提取关键信息...")
            
            # 构建提取prompt
            prompt = self._build_extraction_prompt(transcription_text, video_title)
            
            # 调用LLM
            messages = [
                {"role": "user", "content": prompt}
            ]
            
            response, tokens_used, finish_reason = self.llm.call(
                message_list=messages,
                temperature=0.1,
                max_tokens=8000,
                thinking_budget=8000,  # 确保在支持范围内 (1-24576)
                response_mime_type="application/json"
            )
            
            logger.info(f"💰 LLM调用完成，使用tokens: {tokens_used}")
            
            if finish_reason != "stop":
                logger.warning(f"⚠️ LLM调用未正常结束: {finish_reason}")
            
            # 解析JSON响应
            try:
                extracted_info = json.loads(response)
                extracted_info["extraction_method"] = "gemini_llm"
                extracted_info["tokens_used"] = tokens_used
                
                logger.info("✅ 信息提取成功")
                return extracted_info
                
            except json.JSONDecodeError as e:
                logger.error(f"❌ JSON解析失败: {e}")
                logger.info("📝 原始响应:", response[:500] + "..." if len(response) > 500 else response)
                return self._extract_without_llm(transcription_text, video_title)
                
        except Exception as e:
            logger.error(f"❌ LLM信息提取失败: {e}")
            return self._extract_without_llm(transcription_text, video_title)
    
    def _build_extraction_prompt(self, text: str, title: str) -> str:
        """构建信息提取的prompt"""
        # 尝试从prompts目录读取模板
        prompt_file = Path(__file__).parent.parent / "prompts" / "financial_extraction_prompt.txt"
        
        if prompt_file.exists():
            try:
                with open(prompt_file, 'r', encoding='utf-8') as f:
                    prompt_template = f.read()
                # 替换模板中的占位符
                prompt = prompt_template.format(title=title, text=text)
                logger.info(f"✅ 使用外部prompt模板: {prompt_file}")
                return prompt
            except Exception as e:
                raise RuntimeError(f"⚠️ 读取prompt模板失败, prompt_file: {prompt_file}, error: {e}")
    
    def _extract_without_llm(self, text: str, title: str) -> Dict[str, Any]:
        """不使用LLM的基础信息提取"""
        logger.info("📝 使用基础方法提取信息...")
        
        # 简单的关键词提取
        stocks_mentioned = self._extract_stock_symbols(text)
        numbers = self._extract_numbers(text)
        
        return {
            "extraction_method": "basic_rules",
            "summary": f"基于视频标题的财经分析内容: {title}",
            "text_length": len(text),
            "stocks_mentioned": stocks_mentioned,
            "numbers_found": numbers[:10],  # 限制数量
            "market_overview": {
                "date": "",
                "major_indices": [],
                "market_sentiment": ""
            },
            "macroeconomic_data": [],
            "stock_analysis": [],
            "key_events": [],
            "investment_advice": [],
            "risks_and_warnings": [],
            "note": "使用基础规则提取，信息有限。建议配置Gemini LLM获得更详细的分析。"
        }
    
    def _extract_stock_symbols(self, text: str) -> List[str]:
        """提取股票代码"""
        import re
        
        # 常见美股代码模式
        patterns = [
            r'\b([A-Z]{1,5})\b',  # 1-5个大写字母的股票代码
            r'特斯拉|TSLA',
            r'苹果|AAPL', 
            r'谷歌|GOOGL|GOOG',
            r'微软|MSFT',
            r'亚马逊|AMZN',
            r'英伟达|NVDA',
            r'Meta|META',
            r'博通|AVGO',
            r'LULU'
        ]
        
        stocks = set()
        for pattern in patterns:
            matches = re.findall(pattern, text)
            stocks.update(matches)
        
        # 过滤掉常见的非股票词汇
        exclude = {'AND', 'THE', 'FOR', 'ARE', 'YOU', 'ALL', 'BUT', 'NOT', 'CAN', 'HAD', 'HER', 'WAS', 'ONE', 'OUR', 'OUT', 'DAY', 'GET', 'HAS', 'HIM', 'HIS', 'HOW', 'ITS', 'NEW', 'NOW', 'OLD', 'SEE', 'TWO', 'WHO', 'BOY', 'DID', 'DOWN', 'EACH', 'FEW', 'FROM', 'HAVE', 'HERE', 'INTO', 'JUST', 'LIKE', 'LONG', 'MADE', 'MANY', 'OVER', 'SUCH', 'TAKE', 'THAN', 'THEM', 'WELL', 'WERE', 'WHAT', 'WITH', 'WORK'}
        stocks = [s for s in stocks if s not in exclude and len(s) <= 5]
        
        return list(stocks)[:10]  # 限制返回数量
    
    def _extract_numbers(self, text: str) -> List[str]:
        """提取可能的价格和百分比数据"""
        import re
        
        patterns = [
            r'\b\d+\.?\d*%',  # 百分比
            r'\$\d+\.?\d*',   # 价格
            r'\b\d{1,4}\.?\d*块',  # 中文价格描述
            r'\b\d+\.?\d*美元',    # 美元
            r'\b\d+\.?\d*亿',      # 亿
        ]
        
        numbers = []
        for pattern in patterns:
            matches = re.findall(pattern, text)
            numbers.extend(matches)
        
        return numbers
    
    def save_extracted_info(self, info: Dict[str, Any], output_path: str) -> bool:
        """
        保存提取的信息到JSON文件
        
        Args:
            info: 提取的信息字典
            output_path: 输出文件路径
            
        Returns:
            是否保存成功
        """
        try:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(info, f, ensure_ascii=False, indent=2)
            
            logger.info(f"💾 提取信息已保存到: {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"❌ 保存信息失败: {e}")
            return False


def extract_financial_info(transcription_text: str, 
                         video_title: str = "", 
                         output_path: Optional[str] = None) -> Dict[str, Any]:
    """
    便捷函数：提取财经信息
    
    Args:
        transcription_text: 转录文本
        video_title: 视频标题
        output_path: 可选的输出文件路径
        
    Returns:
        提取的信息字典
    """
    extractor = FinancialInfoExtractor()
    info = extractor.extract_key_info(transcription_text, video_title)
    
    if output_path:
        extractor.save_extracted_info(info, output_path)
    
    return info


def test_with_real_transcription():
    """使用真实的转录文本测试LLM信息提取功能"""
    # 读取真实的转录文本
    transcription_file = Path(__file__).parent.parent / "downloads" / "2025-09-09" / "transcription" / "视野环球财经-2025-09-09.txt"
    
    if not transcription_file.exists():
        print(f"❌ 转录文件不存在: {transcription_file}")
        return
    
    try:
        with open(transcription_file, 'r', encoding='utf-8') as f:
            real_transcription = f.read()
        
        print("🧪 使用真实转录文本测试LLM信息提取功能...")
        print(f"📄 转录文本长度: {len(real_transcription)} 字符")
        print("="*60)
        
        # 提取信息
        extractor = FinancialInfoExtractor()
        result = extractor.extract_key_info(
            transcription_text=real_transcription,
            video_title="美股 NVDA获得部分H20许可！APP、HOOD更新，进标普500！MSTR再落选，技术风险！UNH临门一脚！"
        )
        
        # 保存结果
        output_file = Path(__file__).parent.parent / "downloads" / "2025-09-09" / "analysis" / "视野环球财经-2025-09-09_analysis2.json"
        extractor.save_extracted_info(result, str(output_file))
        
        # 显示提取结果摘要
        print("✅ 信息提取完成!")
        print("="*60)
        
        print(f"🤖 提取方法: {result.get('extraction_method', 'unknown')}")
        
        if result.get('summary'):
            print(f"📋 内容摘要: {result['summary']}")
        
        # 显示市场概况
        market_overview = result.get('market_overview', {})
        if market_overview.get('major_indices'):
            print(f"\n📈 主要指数:")
            for index in market_overview['major_indices'][:3]:  # 显示前3个
                print(f"  • {index.get('name', 'N/A')}: {index.get('performance', 'N/A')}")
        
        # 显示宏观数据
        macro_data = result.get('macroeconomic_data', [])
        if macro_data:
            print(f"\n🌍 宏观经济数据 ({len(macro_data)}条):")
            for data in macro_data[:3]:  # 显示前3条
                print(f"  • {data.get('indicator', 'N/A')}: {data.get('value', 'N/A')}")
        
        # 显示股票分析
        stock_analysis = result.get('stock_analysis', [])
        if stock_analysis:
            print(f"\n📊 个股分析 ({len(stock_analysis)}只股票):")
            for stock in stock_analysis:
                symbol = stock.get('symbol', 'N/A')
                company = stock.get('company_name', 'N/A')
                outlook = stock.get('outlook', 'N/A')
                print(f"  🏢 {symbol} ({company})")
                print(f"     观点: {outlook}")
                
                # 显示关键点位
                price_levels = stock.get('price_levels', {})
                if price_levels.get('support'):
                    print(f"     支撑位: {', '.join(price_levels['support'])}")
                if price_levels.get('resistance'):
                    print(f"     阻力位: {', '.join(price_levels['resistance'])}")
        
        # 显示投资建议
        advice = result.get('investment_advice', [])
        if advice:
            print(f"\n💡 投资建议 ({len(advice)}条):")
            for item in advice[:3]:  # 显示前3条
                print(f"  • {item}")
        
        # 显示风险警示
        risks = result.get('risks_and_warnings', [])
        if risks:
            print(f"\n⚠️ 风险提示 ({len(risks)}条):")
            for risk in risks[:2]:  # 显示前2条
                print(f"  • {risk}")
        
        print("="*60)
        print(f"💾 详细结果已保存到: {output_file}")
        
        # 显示tokens使用情况
        if result.get('tokens_used'):
            print(f"💰 LLM Tokens 使用量: {result['tokens_used']}")
        
    except Exception as e:
        logger.error(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # 使用真实转录文本测试
    test_with_real_transcription()
