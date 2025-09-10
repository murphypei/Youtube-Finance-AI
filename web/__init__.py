"""
Web展示模块
包含Web仪表板和分析结果汇总功能
"""

from web.analyzer import FinancialAnalyzer
from web.web_dashboard import FinanceDashboard

__all__ = [
    'FinancialAnalyzer',
    'FinanceDashboard'
]
