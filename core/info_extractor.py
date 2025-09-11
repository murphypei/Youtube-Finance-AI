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
        
        # 定义财经信息提取的JSON schema
        self.response_schema = self._create_financial_schema()
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
        
        # 使用重试机制进行提取
        return self._extract_with_retry(transcription_text, video_title, max_attempts=3)
    
    def _extract_with_retry(self, transcription_text: str, video_title: str, max_attempts: int = 3) -> Dict[str, Any]:
        """
        带重试的信息提取
        
        Args:
            transcription_text: 转录文本
            video_title: 视频标题  
            max_attempts: 最大尝试次数
            
        Returns:
            提取的信息字典
        """
        last_error = None
        
        for attempt in range(max_attempts):
            try:
                logger.info(f"🤖 开始使用Gemini提取关键信息... (第 {attempt + 1}/{max_attempts} 次)")
                
                # 构建提取prompt
                prompt = self._build_extraction_prompt(transcription_text, video_title)
                
                # 调用LLM
                messages = [{"role": "user", "content": prompt}]
                
                response, tokens_used, finish_reason = self.llm.call(
                    message_list=messages,
                    temperature=0.1,
                    max_tokens=8000,
                    thinking_budget=8000,
                    response_mime_type="application/json",
                    response_schema=self.response_schema
                )
                
                logger.info(f"💰 LLM调用完成，使用tokens: {tokens_used}")
                
                if finish_reason != "stop":
                    logger.warning(f"⚠️ LLM调用未正常结束: {finish_reason}")
                    # 如果不是正常结束，但有响应内容，仍然尝试解析
                    if not response.strip():
                        raise Exception(f"LLM调用未正常结束且响应为空: {finish_reason}")
                
                # 解析JSON响应 - 多次尝试
                extracted_info = self._parse_json_response(response, attempt + 1)
                if extracted_info:
                    extracted_info["extraction_method"] = "gemini_llm"
                    extracted_info["tokens_used"] = tokens_used
                    extracted_info["attempts_used"] = attempt + 1
                    
                    logger.info(f"✅ 信息提取成功 (第 {attempt + 1} 次尝试)")
                    return extracted_info
                else:
                    raise Exception("JSON解析失败")
                    
            except Exception as e:
                last_error = e
                logger.warning(f"⚠️ 第 {attempt + 1} 次提取失败: {e}")
                
                if attempt < max_attempts - 1:
                    import time
                    wait_time = 2 ** attempt  # 指数退避: 1, 2, 4秒
                    logger.info(f"🔄 等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)
        
        logger.error(f"❌ 所有提取尝试都失败了，最后错误: {last_error}")
        logger.info("🔄 回退到基础规则提取")
        return self._extract_without_llm(transcription_text, video_title)
    
    def _parse_json_response(self, response: str, attempt_num: int) -> Optional[Dict[str, Any]]:
        """
        解析JSON响应，支持多种格式清理
        
        Args:
            response: 原始响应
            attempt_num: 尝试次数
            
        Returns:
            解析后的字典或None
        """
        if not response.strip():
            logger.warning("响应为空")
            return None
        
        # 尝试多种方式清理和解析JSON
        json_attempts = [
            response.strip(),  # 原始响应
            response.strip().strip('```json').strip('```'),  # 移除markdown代码块
            response[response.find('{'):response.rfind('}') + 1] if '{' in response and '}' in response else response,  # 提取JSON部分
        ]
        
        for i, json_str in enumerate(json_attempts):
            try:
                if json_str.strip():
                    parsed = json.loads(json_str)
                    if i > 0:
                        logger.info(f"JSON解析成功 (使用第 {i + 1} 种清理方法)")
                    return parsed
            except json.JSONDecodeError as e:
                if i == 0:
                    logger.debug(f"第 {i + 1} 种JSON解析失败: {e}")
                continue
        
        # 记录失败详情
        logger.error(f"所有JSON解析方法都失败了")
        logger.info(f"原始响应 (前500字符): {response[:500]}")
        return None
    
    def _create_financial_schema(self) -> Dict[str, Any]:
        """
        创建财经信息提取的JSON schema
        
        Returns:
            完整的JSON schema定义
        """
        return {
            "type": "object",
            "required": [
                "summary",
                "market_overview", 
                "macroeconomic_data",
                "stock_analysis",
                "key_events",
                "investment_advice",
                "risks_and_warnings"
            ],
            "properties": {
                "summary": {
                    "type": "string",
                    "description": "对整个财经分析内容的简明总结"
                },
                "market_overview": {
                    "type": "object",
                    "required": ["date", "major_indices", "market_sentiment"],
                    "properties": {
                        "date": {
                            "type": "string",
                            "description": "分析日期，格式YYYY-MM-DD"
                        },
                        "major_indices": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "required": ["name", "performance"],
                                "properties": {
                                    "name": {
                                        "type": "string",
                                        "description": "指数名称，如S&P 500, 纳斯达克等"
                                    },
                                    "performance": {
                                        "type": "string",
                                        "description": "当日表现描述"
                                    },
                                    "current_level": {
                                        "type": "string",
                                        "description": "当前点位或价格"
                                    },
                                    "key_levels": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                        "description": "关键技术位"
                                    },
                                    "analysis": {
                                        "type": "string",
                                        "description": "技术分析和走势解读"
                                    }
                                }
                            },
                            "description": "主要市场指数分析"
                        },
                        "market_sentiment": {
                            "type": "string",
                            "description": "整体市场情绪和驱动因素"
                        }
                    }
                },
                "macroeconomic_data": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["indicator", "impact"],
                        "properties": {
                            "indicator": {
                                "type": "string",
                                "description": "宏观经济指标名称"
                            },
                            "actual_value": {
                                "type": "string",
                                "description": "实际公布值"
                            },
                            "expected_value": {
                                "type": "string",
                                "description": "市场预期值"
                            },
                            "previous_value": {
                                "type": "string",
                                "description": "前值"
                            },
                            "impact": {
                                "type": "string",
                                "description": "对市场的影响分析"
                            },
                            "interpretation": {
                                "type": "string",
                                "description": "数据解读和意义"
                            }
                        }
                    },
                    "description": "宏观经济数据和分析"
                },
                "stock_analysis": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["symbol", "key_points"],
                        "properties": {
                            "symbol": {
                                "type": "string",
                                "description": "股票代码或ETF代码"
                            },
                            "company_name": {
                                "type": "string",
                                "description": "公司或产品全名"
                            },
                            "current_price": {
                                "type": "string",
                                "description": "当前价格或价格区间"
                            },
                            "price_change": {
                                "type": "string",
                                "description": "价格变化"
                            },
                            "key_points": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "关键分析要点"
                            },
                            "price_levels": {
                                "type": "object",
                                "properties": {
                                    "support": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                        "description": "支撑位"
                                    },
                                    "resistance": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                        "description": "阻力位"
                                    },
                                    "target": {
                                        "type": "array", 
                                        "items": {"type": "string"},
                                        "description": "目标位"
                                    }
                                }
                            },
                            "recommendation": {
                                "type": "string",
                                "enum": ["买入", "持有", "卖出", "观望"],
                                "description": "投资建议"
                            },
                            "risk_reward_ratio": {
                                "type": "string",
                                "description": "风险收益比"
                            },
                            "analyst_notes": {
                                "type": "string",
                                "description": "分析师备注"
                            }
                        }
                    },
                    "description": "个股分析"
                },
                "key_events": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["event", "impact"],
                        "properties": {
                            "event": {
                                "type": "string",
                                "description": "关键事件描述"
                            },
                            "date": {
                                "type": "string",
                                "description": "事件日期"
                            },
                            "impact": {
                                "type": "string",
                                "description": "对市场的影响"
                            },
                            "category": {
                                "type": "string",
                                "enum": ["财报", "政策", "经济数据", "企业行为", "其他"],
                                "description": "事件类别"
                            }
                        }
                    },
                    "description": "影响市场的关键事件"
                },
                "investment_advice": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["advice", "timeframe"],
                        "properties": {
                            "advice": {
                                "type": "string",
                                "description": "具体投资建议"
                            },
                            "timeframe": {
                                "type": "string",
                                "enum": ["短期", "中期", "长期"],
                                "description": "建议的时间框架"
                            },
                            "rationale": {
                                "type": "string",
                                "description": "建议的理由"
                            },
                            "target_audience": {
                                "type": "string",
                                "description": "目标投资者类型"
                            }
                        }
                    },
                    "description": "投资建议"
                },
                "risks_and_warnings": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["risk", "severity"],
                        "properties": {
                            "risk": {
                                "type": "string",
                                "description": "风险描述"
                            },
                            "severity": {
                                "type": "string",
                                "enum": ["低", "中", "高"],
                                "description": "风险严重程度"
                            },
                            "probability": {
                                "type": "string",
                                "enum": ["低", "中", "高"],
                                "description": "风险发生概率"
                            },
                            "mitigation": {
                                "type": "string",
                                "description": "风险缓解措施"
                            }
                        }
                    },
                    "description": "风险提示和警告"
                }
            }
        }
    
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
    transcription_file = Path(__file__).parent.parent / "downloads" / "rhino_finance" / "2025-09-10" / "transcription" / "rhino_ZKo41ja8rD0.txt"
    
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
        output_file = Path(__file__).parent.parent / "downloads" / "rhino_finance" / "2025-09-10" / "analysis" / "rhino_ZKo41ja8rD0_analysis2.json"
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
