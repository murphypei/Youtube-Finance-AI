"""
财经分析结果汇总和聚合处理模块
对批量处理的结果进行日期聚合、股票信息整理和宏观数据汇总
"""

import json
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from collections import defaultdict
import re

class FinancialAnalyzer:
    """财经分析结果处理器"""
    
    def __init__(self, data_dir: str = None):
        """
        初始化分析器
        
        Args:
            data_dir: 数据目录路径，默认为downloads/rhino_finance
        """
        if data_dir is None:
            self.data_dir = Path.cwd() / "downloads" / "rhino_finance"
        else:
            self.data_dir = Path(data_dir)
        
        print(f"📊 初始化财经分析器")
        print(f"📁 数据目录: {self.data_dir}")
    
    def load_batch_results(self, results_file: str = None) -> Dict[str, Any]:
        """
        加载批量处理结果文件
        
        Args:
            results_file: 结果文件路径，为None时加载最新的结果文件
            
        Returns:
            批量处理结果数据
        """
        if results_file is None:
            # 查找最新的批量结果文件
            batch_files = list(self.data_dir.glob("batch_results_*.json"))
            if not batch_files:
                raise FileNotFoundError("未找到批量处理结果文件")
            
            # 按时间排序，获取最新的
            batch_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            results_file = batch_files[0]
            print(f"📄 加载最新批量结果: {results_file.name}")
        else:
            results_file = Path(results_file)
        
        with open(results_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def collect_all_analysis_data(self) -> List[Dict[str, Any]]:
        """
        收集所有日期目录下的分析结果
        
        Returns:
            所有分析结果的列表
        """
        print("🔍 收集所有分析数据...")
        
        all_data = []
        
        # 遍历所有日期目录
        for date_dir in self.data_dir.iterdir():
            if not date_dir.is_dir() or not re.match(r'\d{4}-\d{2}-\d{2}', date_dir.name):
                continue
            
            analysis_dir = date_dir / 'analysis'
            if not analysis_dir.exists():
                continue
            
            print(f"📅 处理日期: {date_dir.name}")
            
            # 加载该日期的所有分析文件
            for analysis_file in analysis_dir.glob("*.json"):
                try:
                    with open(analysis_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        
                    # 添加元数据
                    data['file_date'] = date_dir.name
                    data['file_name'] = analysis_file.name
                    data['file_path'] = str(analysis_file)
                    
                    all_data.append(data)
                    
                except Exception as e:
                    print(f"⚠️ 读取 {analysis_file} 失败: {e}")
        
        print(f"✅ 收集到 {len(all_data)} 份分析数据")
        return all_data
    
    def aggregate_by_date(self, analysis_data: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        按日期聚合分析数据
        
        Args:
            analysis_data: 分析数据列表
            
        Returns:
            按日期聚合的数据字典
        """
        print("📊 按日期聚合数据...")
        
        date_groups = defaultdict(list)
        
        for data in analysis_data:
            file_date = data.get('file_date', 'unknown')
            date_groups[file_date].append(data)
        
        # 按日期排序
        sorted_dates = dict(sorted(date_groups.items(), reverse=True))
        
        for date, items in sorted_dates.items():
            print(f"📅 {date}: {len(items)} 份分析")
        
        return sorted_dates
    
    def extract_macro_news(self, date_groups: Dict[str, List[Dict[str, Any]]], days: int = 1) -> List[Dict[str, Any]]:
        """
        提取最近几天的宏观新闻
        
        Args:
            date_groups: 按日期分组的数据
            days: 提取天数
            
        Returns:
            宏观新闻列表
        """
        print(f"📰 提取最近 {days} 天的宏观新闻...")
        
        macro_news = []
        processed_dates = 0
        
        for date, items in date_groups.items():
            if processed_dates >= days:
                break
                
            for item in items:
                # 提取宏观经济数据
                macro_data = item.get('macroeconomic_data', [])
                if macro_data:
                    for data_point in macro_data:
                        macro_news.append({
                            'date': date,
                            'source_file': item.get('file_name', ''),
                            'indicator': data_point.get('indicator', ''),
                            'value': data_point.get('actual_value', data_point.get('value', '')),
                            'expected': data_point.get('expected_value', data_point.get('expected', '')),
                            'impact': data_point.get('impact', ''),
                            'description': data_point.get('interpretation', data_point.get('description', ''))
                        })
                
                # 提取关键事件
                key_events = item.get('key_events', [])
                if key_events:
                    for event in key_events:
                        # 如果event是字符串，直接使用；如果是字典，提取相关字段
                        if isinstance(event, str):
                            event_desc = event
                            event_impact = ''
                        elif isinstance(event, dict):
                            event_desc = event.get('description', event.get('event', str(event)))
                            event_impact = event.get('impact', '')
                        else:
                            event_desc = str(event)
                            event_impact = ''
                            
                        macro_news.append({
                            'date': date,
                            'source_file': item.get('file_name', ''),
                            'indicator': '重要事件',
                            'value': event_desc,
                            'expected': '',
                            'impact': event_impact,
                            'description': event_desc
                        })
            
            processed_dates += 1
        
        print(f"✅ 提取到 {len(macro_news)} 条宏观信息")
        return macro_news
    
    def extract_stock_positions(self, date_groups: Dict[str, List[Dict[str, Any]]], days: int = 7) -> List[Dict[str, Any]]:
        """
        提取最近几天的股票点位信息
        
        Args:
            date_groups: 按日期分组的数据
            days: 提取天数
            
        Returns:
            股票点位信息列表
        """
        print(f"📈 提取最近 {days} 天的股票点位信息...")
        
        stock_positions = []
        stock_summary = defaultdict(list)  # 按股票代码汇总
        processed_dates = 0
        
        for date, items in date_groups.items():
            if processed_dates >= days:
                break
                
            for item in items:
                stock_analysis = item.get('stock_analysis', [])
                
                for stock in stock_analysis:
                    symbol = stock.get('symbol', '')
                    company_name = stock.get('company_name', '')
                    
                    # 提取价格信息
                    current_price = stock.get('current_price', '')
                    price_levels = stock.get('price_levels', {})
                    
                    # 支撑阻力位可能在不同字段中
                    support_levels = (price_levels.get('support', []) or 
                                    price_levels.get('support_levels', []) or
                                    [])
                    resistance_levels = (price_levels.get('resistance', []) or 
                                       price_levels.get('resistance_levels', []) or
                                       [])
                    
                    # 提取操作建议 - 尝试多个可能的字段
                    outlook = stock.get('outlook', '')
                    recommendation = stock.get('recommendation', '')
                    analyst_notes = stock.get('analyst_notes', '')
                    
                    # 推断操作类型 - 综合多个字段
                    action = self._determine_action(outlook, recommendation + " " + analyst_notes)
                    
                    position_info = {
                        'date': date,
                        'source_file': item.get('file_name', ''),
                        'symbol': symbol,
                        'company_name': company_name,
                        'current_price': current_price,
                        'support_levels': support_levels,
                        'resistance_levels': resistance_levels,
                        'action': action,
                        'outlook': outlook,
                        'recommendation': recommendation,
                        'key_points': stock.get('key_points', []),
                        'risk_factors': stock.get('risk_factors', [])
                    }
                    
                    stock_positions.append(position_info)
                    stock_summary[symbol].append(position_info)
            
            processed_dates += 1
        
        print(f"✅ 提取到 {len(stock_positions)} 条股票点位信息")
        print(f"📊 涉及 {len(stock_summary)} 只不同股票")
        
        return stock_positions
    
    def _determine_action(self, outlook: str, recommendation: str) -> str:
        """
        根据展望和建议判断操作类型
        
        Args:
            outlook: 展望描述
            recommendation: 建议描述
            
        Returns:
            操作类型: 买入/卖出/持有/观望
        """
        text = (str(outlook) + " " + str(recommendation)).lower()
        
        # 买入信号关键词 - 更全面的关键词
        buy_keywords = [
            '买入', '建议买入', '逢低买入', '增持', '建议增持', 'buy', 'long', 
            '看好', '建议关注', '加仓', '建议加仓', '积极', '强烈推荐', 
            '上涨', '看涨', '建议持有并适度加仓', '强势', '重回上攻'
        ]
        
        # 卖出信号关键词  
        sell_keywords = [
            '卖出', '建议卖出', '减持', '建议减持', 'sell', 'short', 
            '看空', '谨慎', '减仓', '不建议', '超买', '不宜追高',
            '获利了结', '止盈', '规避风险', '破位下行'
        ]
        
        # 持有信号关键词
        hold_keywords = [
            '持有', '维持', 'hold', '长线持有', '保持', '继续持有',
            '稳健', '维持仓位', '不变', '波段'
        ]
        
        # 观望信号关键词
        watch_keywords = [
            '观望', '等待', '暂时观望', '谨慎观望', '静观其变', 
            '等待时机', '暂不操作', '关注', '跟踪'
        ]
        
        # 按优先级匹配
        for keyword in buy_keywords:
            if keyword in text:
                return '买入'
        
        for keyword in sell_keywords:
            if keyword in text:
                return '卖出'
        
        for keyword in hold_keywords:
            if keyword in text:
                return '持有'
                
        for keyword in watch_keywords:
            if keyword in text:
                return '观望'
        
        return '观望'  # 默认
    
    def create_summary_report(self, macro_news: List[Dict[str, Any]], stock_positions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        创建汇总报告
        
        Args:
            macro_news: 宏观新闻列表
            stock_positions: 股票点位列表
            
        Returns:
            汇总报告数据
        """
        print("📋 创建汇总报告...")
        
        # 统计股票操作分布
        action_counts = defaultdict(int)
        for pos in stock_positions:
            action_counts[pos['action']] += 1
        
        # 获取最活跃的股票
        symbol_counts = defaultdict(int)
        for pos in stock_positions:
            if pos['symbol']:
                symbol_counts[pos['symbol']] += 1
        
        most_mentioned = dict(sorted(symbol_counts.items(), key=lambda x: x[1], reverse=True)[:10])
        
        summary = {
            'generated_at': datetime.now().isoformat(),
            'macro_news_count': len(macro_news),
            'stock_positions_count': len(stock_positions),
            'action_distribution': dict(action_counts),
            'most_mentioned_stocks': most_mentioned,
            'latest_macro_news': macro_news[:5],  # 最新5条
            'active_stock_positions': stock_positions[:10],  # 最活跃10只
            'macro_news': macro_news,
            'stock_positions': stock_positions
        }
        
        print(f"✅ 报告生成完成")
        print(f"📰 宏观新闻: {len(macro_news)} 条")
        print(f"📈 股票点位: {len(stock_positions)} 条")
        print(f"🎯 操作分布: {dict(action_counts)}")
        
        return summary
    
    def save_summary_report(self, summary: Dict[str, Any], filename: str = None) -> str:
        """
        保存汇总报告
        
        Args:
            summary: 汇总报告数据
            filename: 文件名，为None时自动生成
            
        Returns:
            保存的文件路径
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"summary_report_{timestamp}.json"
        
        output_file = self.data_dir / filename
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        print(f"💾 汇总报告已保存: {output_file}")
        return str(output_file)


def main():
    """主函数，生成分析汇总报告"""
    import argparse
    
    parser = argparse.ArgumentParser(description="📊 财经分析结果汇总工具")
    parser.add_argument('--data-dir', help='数据目录路径')
    parser.add_argument('--macro-days', type=int, default=1, help='宏观新闻提取天数 (默认: 1)')
    parser.add_argument('--stock-days', type=int, default=7, help='股票点位提取天数 (默认: 7)')
    
    args = parser.parse_args()
    
    print("📊 财经分析结果汇总工具")
    print("=" * 40)
    
    # 初始化分析器
    analyzer = FinancialAnalyzer(args.data_dir)
    
    # 收集分析数据
    analysis_data = analyzer.collect_all_analysis_data()
    if not analysis_data:
        print("❌ 未找到分析数据")
        return
    
    # 按日期聚合
    date_groups = analyzer.aggregate_by_date(analysis_data)
    
    # 提取宏观新闻和股票点位
    macro_news = analyzer.extract_macro_news(date_groups, args.macro_days)
    stock_positions = analyzer.extract_stock_positions(date_groups, args.stock_days)
    
    # 创建汇总报告
    summary = analyzer.create_summary_report(macro_news, stock_positions)
    
    # 保存报告
    report_file = analyzer.save_summary_report(summary)
    
    print(f"\n🎉 汇总完成!")
    print(f"📄 报告文件: {report_file}")


if __name__ == "__main__":
    main()
