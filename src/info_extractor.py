"""
财经信息提取器
从ASR转录的文本中提取关键投资信息，包括宏观数据、个股分析、关键点位等
"""

import sys
import json
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

# 设置日志
logger = logging.getLogger(__name__)

# 尝试导入gemini_llm
try:
    from src.gemini_llm import GeminiLLM, gemini_config
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
                logger.warning(f"⚠️ 读取prompt模板失败，使用内置模板: {e}")
        
        # 如果外部模板不可用，使用内置模板
        prompt = f"""你是一位专业的金融分析师，请从以下财经视频的转录文本中提取关键投资信息。

视频标题: {title}

转录文本:
{text}

请仔细分析转录内容，提取以下信息并以严格的JSON格式返回：

{{
    "summary": "用2-3句话概括视频的核心内容和主要观点",
    "market_overview": {{
        "date": "视频讨论的具体日期(YYYY-MM-DD格式)",
        "major_indices": [
            {{
                "name": "指数名称(如S&P500、NASDAQ、Russell等)",
                "performance": "涨跌幅度，包含具体数字和百分比",
                "current_level": "当前点位或价格",
                "key_levels": ["技术关键位置"],
                "analysis": "对该指数的具体分析观点"
            }}
        ],
        "market_sentiment": "整体市场情绪和趋势判断"
    }},
    "macroeconomic_data": [
        {{
            "indicator": "经济指标名称(如非农就业、CPI、PMI等)",
            "actual_value": "实际公布数值",
            "expected_value": "市场预期数值",
            "previous_value": "前值",
            "impact": "对市场的具体影响分析",
            "interpretation": "数据解读"
        }}
    ],
    "stock_analysis": [
        {{
            "symbol": "股票代码(如TSLA、AAPL、NVDA等)",
            "company_name": "公司全名",
            "current_price": "当前股价",
            "price_change": "涨跌幅",
            "key_points": [
                "关键分析要点，包括业绩、新闻、技术面等"
            ],
            "price_levels": {{
                "support": ["支撑位价格"],
                "resistance": ["阻力位价格"],
                "target": ["目标价位"]
            }},
            "financial_data": {{
                "revenue": "营收数据",
                "earnings": "盈利数据",
                "guidance": "业绩指引"
            }},
            "outlook": "未来走势判断和投资观点",
            "risk_factors": ["主要风险因素"]
        }}
    ],
    "key_events": [
        {{
            "event": "重要事件详细描述",
            "companies_affected": ["受影响的公司"],
            "date": "事件日期",
            "impact": "预期影响程度和方向",
            "significance": "事件重要性评估"
        }}
    ],
    "investment_advice": [
        {{
            "type": "建议类型(买入/卖出/持有/观望)",
            "target": "针对对象(个股/板块/市场)",
            "rationale": "建议理由",
            "time_horizon": "建议期限",
            "risk_level": "风险等级"
        }}
    ],
    "technical_analysis": [
        {{
            "asset": "分析对象",
            "pattern": "技术形态",
            "indicators": "技术指标信号",
            "trend": "趋势判断",
            "entry_exit_points": "进出场点位"
        }}
    ],
    "risks_and_warnings": [
        {{
            "risk_type": "风险类型",
            "description": "风险详细描述",
            "probability": "发生概率评估",
            "potential_impact": "潜在影响",
            "mitigation": "应对策略"
        }}
    ],
    "fed_policy": {{
        "interest_rate_outlook": "利率前景",
        "policy_implications": "政策影响",
        "market_expectations": "市场预期"
    }},
    "sector_rotation": [
        {{
            "from_sector": "资金流出板块",
            "to_sector": "资金流入板块",
            "reason": "轮动原因",
            "duration": "预期持续时间"
        }}
    ]
}}

提取要求：
1. 只提取文本中明确提及的信息，不要推测或编造
2. 数字数据要精确，包含单位
3. 股票代码统一用美股格式
4. 价格数据保留小数点
5. 日期格式为YYYY-MM-DD
6. 如果某个字段没有信息，使用空数组[]或空字符串""
7. 确保返回有效JSON格式
8. 专注于投资价值高的信息
9. 提取具体的数字、百分比、价格点位
10. 识别中文股票名称对应的美股代码(如特斯拉->TSLA，苹果->AAPL，博通->AVGO，英伟达->NVDA)

特别关注：
- 具体的股价和涨跌幅
- 财报数据(营收、利润、指引)
- 技术分析的关键点位
- 宏观经济数据的实际值vs预期值
- 投资建议的具体操作和理由
- 风险提示的具体内容

请开始分析提取："""
        return prompt
    
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
    transcription_file = Path(__file__).parent.parent / "downloads" / "test_whisper_transcribe.txt"
    
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
            video_title="美股 标普新高又跌不动了？TSLA马斯克很硬气！LULU业绩加速衰退！AVGO大客户助力继续冲锋！"
        )
        
        # 保存结果
        output_file = Path(__file__).parent.parent / "downloads" / "extracted_info_test.json"
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
