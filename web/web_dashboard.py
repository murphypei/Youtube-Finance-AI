"""
财经分析结果展示网站
使用Flask创建一个简洁的仪表板来展示分析结果
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

try:
    from flask import Flask, render_template, jsonify, request, send_from_directory
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
    print("⚠️ Flask未安装，请运行: pip install flask")

from web.analyzer import FinancialAnalyzer

class FinanceDashboard:
    """财经分析仪表板"""
    
    def __init__(self, data_dir: str = None, debug: bool = True):
        """
        初始化仪表板
        
        Args:
            data_dir: 数据目录路径
            debug: 调试模式
        """
        if not FLASK_AVAILABLE:
            raise ImportError("Flask is required for web dashboard")
        
        self.app = Flask(__name__, 
                        template_folder='../templates',
                        static_folder='../static')
        self.app.config['DEBUG'] = debug
        
        # 初始化分析器
        self.analyzer = FinancialAnalyzer(data_dir)
        
        # 设置路由
        self._setup_routes()
        
        print("🌐 财经仪表板初始化完成")
        print(f"📁 数据目录: {self.analyzer.data_dir}")
    
    def _setup_routes(self):
        """设置路由"""
        
        @self.app.route('/')
        def index():
            """主页"""
            return render_template('dashboard.html')
        
        @self.app.route('/api/data')
        def get_data():
            """获取分析数据API"""
            try:
                # 收集最新数据
                analysis_data = self.analyzer.collect_all_analysis_data()
                if not analysis_data:
                    return jsonify({'error': 'No analysis data found'})
                
                # 按日期聚合
                date_groups = self.analyzer.aggregate_by_date(analysis_data)
                
                # 提取数据
                macro_news = self.analyzer.extract_macro_news(date_groups, days=1)
                stock_positions = self.analyzer.extract_stock_positions(date_groups, days=7)
                
                # 创建汇总
                summary = self.analyzer.create_summary_report(macro_news, stock_positions)
                
                return jsonify({
                    'success': True,
                    'data': summary,
                    'updated_at': datetime.now().isoformat()
                })
                
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                })
        
        @self.app.route('/api/refresh')
        def refresh_data():
            """刷新数据API"""
            return self.get_data()
    
    def run(self, host: str = '0.0.0.0', port: int = 5000):
        """启动Web服务器"""
        print(f"🚀 启动财经仪表板...")
        print(f"🌐 访问地址: http://{host}:{port}")
        
        self.app.run(host=host, port=port, debug=self.app.config['DEBUG'])


# 创建模板目录和文件
def create_templates():
    """创建模板文件"""
    templates_dir = Path.cwd() / "templates"
    static_dir = Path.cwd() / "static"
    
    templates_dir.mkdir(exist_ok=True)
    static_dir.mkdir(exist_ok=True)
    
    # 创建主模板
    dashboard_html = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🦏 Rhino Finance 财经分析仪表板</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #f5f6fa;
            color: #2c3e50;
            line-height: 1.6;
        }
        
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 1.5rem 0;
            text-align: center;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .header h1 {
            font-size: 2.5rem;
            margin-bottom: 0.5rem;
        }
        
        .header p {
            font-size: 1.1rem;
            opacity: 0.9;
        }
        
        .container {
            max-width: 1400px;
            margin: 2rem auto;
            padding: 0 1rem;
        }
        
        .dashboard-grid {
            display: grid;
            grid-template-columns: 1fr 2fr;
            gap: 2rem;
            margin-bottom: 2rem;
        }
        
        .card {
            background: white;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.07);
            overflow: hidden;
            border: 1px solid #e1e5e9;
        }
        
        .card-header {
            background: #f8f9fa;
            padding: 1.2rem;
            border-bottom: 1px solid #e1e5e9;
            display: flex;
            justify-content: between;
            align-items: center;
        }
        
        .card-header h2 {
            font-size: 1.4rem;
            color: #2c3e50;
            margin: 0;
        }
        
        .card-content {
            padding: 1.5rem;
        }
        
        .macro-news-item {
            padding: 1rem;
            border-left: 4px solid #3498db;
            margin-bottom: 1rem;
            background: #f8f9fa;
            border-radius: 0 8px 8px 0;
        }
        
        .macro-news-item:last-child {
            margin-bottom: 0;
        }
        
        .macro-news-item .indicator {
            font-weight: 600;
            color: #2c3e50;
            margin-bottom: 0.3rem;
        }
        
        .macro-news-item .value {
            font-size: 1.1rem;
            margin-bottom: 0.3rem;
        }
        
        .macro-news-item .date {
            font-size: 0.85rem;
            color: #7f8c8d;
        }
        
        .stock-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.9rem;
        }
        
        .stock-table th,
        .stock-table td {
            padding: 0.8rem;
            text-align: left;
            border-bottom: 1px solid #e1e5e9;
        }
        
        .stock-table th {
            background: #f8f9fa;
            font-weight: 600;
            color: #2c3e50;
        }
        
        .stock-table tbody tr:hover {
            background: #f8f9fa;
        }
        
        .action-badge {
            display: inline-block;
            padding: 0.3rem 0.8rem;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 600;
            text-align: center;
        }
        
        .action-buy { background: #d4edda; color: #155724; }
        .action-sell { background: #f8d7da; color: #721c24; }
        .action-hold { background: #fff3cd; color: #856404; }
        .action-watch { background: #e2e3e5; color: #383d41; }
        
        .price-levels {
            font-size: 0.8rem;
            line-height: 1.3;
        }
        
        .support { color: #28a745; }
        .resistance { color: #dc3545; }
        
        .loading {
            text-align: center;
            padding: 2rem;
            font-style: italic;
            color: #7f8c8d;
        }
        
        .error {
            background: #f8d7da;
            color: #721c24;
            padding: 1rem;
            border-radius: 8px;
            margin: 1rem 0;
        }
        
        .refresh-btn {
            background: #3498db;
            color: white;
            border: none;
            padding: 0.6rem 1.2rem;
            border-radius: 6px;
            cursor: pointer;
            font-size: 0.9rem;
            transition: background 0.3s;
        }
        
        .refresh-btn:hover {
            background: #2980b9;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin-bottom: 2rem;
        }
        
        .stat-card {
            background: white;
            padding: 1.5rem;
            border-radius: 12px;
            text-align: center;
            box-shadow: 0 4px 6px rgba(0,0,0,0.07);
        }
        
        .stat-number {
            font-size: 2rem;
            font-weight: 700;
            color: #3498db;
            margin-bottom: 0.5rem;
        }
        
        .stat-label {
            color: #7f8c8d;
            font-size: 0.9rem;
        }
        
        @media (max-width: 768px) {
            .dashboard-grid {
                grid-template-columns: 1fr;
            }
            
            .header h1 {
                font-size: 2rem;
            }
            
            .stock-table {
                font-size: 0.8rem;
            }
            
            .stock-table th,
            .stock-table td {
                padding: 0.5rem;
            }
        }
        
        .last-updated {
            text-align: center;
            color: #7f8c8d;
            font-size: 0.9rem;
            margin-top: 2rem;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🦏 Rhino Finance</h1>
        <p>财经分析智能仪表板</p>
    </div>
    
    <div class="container">
        <!-- 统计概览 -->
        <div class="stats-grid" id="statsGrid">
            <div class="stat-card">
                <div class="stat-number" id="macroCount">-</div>
                <div class="stat-label">宏观新闻</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" id="stockCount">-</div>
                <div class="stat-label">股票分析</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" id="buyCount">-</div>
                <div class="stat-label">买入建议</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" id="sellCount">-</div>
                <div class="stat-label">卖出建议</div>
            </div>
        </div>
        
        <!-- 主要内容 -->
        <div class="dashboard-grid">
            <!-- 宏观新闻 -->
            <div class="card">
                <div class="card-header">
                    <h2>📰 最新宏观新闻</h2>
                    <button class="refresh-btn" onclick="refreshData()">刷新</button>
                </div>
                <div class="card-content">
                    <div id="macroNews" class="loading">正在加载数据...</div>
                </div>
            </div>
            
            <!-- 股票点位分析 -->
            <div class="card">
                <div class="card-header">
                    <h2>📈 股票点位分析 (近7天)</h2>
                </div>
                <div class="card-content">
                    <div id="stockPositions" class="loading">正在加载数据...</div>
                </div>
            </div>
        </div>
        
        <div class="last-updated" id="lastUpdated"></div>
    </div>

    <script>
        // 数据加载和显示
        async function loadData() {
            try {
                const response = await fetch('/api/data');
                const result = await response.json();
                
                if (result.success) {
                    displayData(result.data);
                    document.getElementById('lastUpdated').textContent = 
                        `最后更新: ${new Date(result.updated_at).toLocaleString()}`;
                } else {
                    showError('数据加载失败: ' + result.error);
                }
            } catch (error) {
                showError('网络连接失败: ' + error.message);
            }
        }
        
        function displayData(data) {
            // 更新统计数据
            document.getElementById('macroCount').textContent = data.macro_news_count || 0;
            document.getElementById('stockCount').textContent = data.stock_positions_count || 0;
            document.getElementById('buyCount').textContent = data.action_distribution['买入'] || 0;
            document.getElementById('sellCount').textContent = data.action_distribution['卖出'] || 0;
            
            // 显示宏观新闻
            displayMacroNews(data.macro_news || []);
            
            // 显示股票点位
            displayStockPositions(data.stock_positions || []);
        }
        
        function displayMacroNews(macroNews) {
            const container = document.getElementById('macroNews');
            
            if (macroNews.length === 0) {
                container.innerHTML = '<div class="loading">暂无宏观新闻数据</div>';
                return;
            }
            
            const html = macroNews.slice(0, 10).map(news => `
                <div class="macro-news-item">
                    <div class="indicator">${news.indicator || '重要指标'}</div>
                    <div class="value">${news.value || news.description || '-'}</div>
                    ${news.expected ? `<div style="font-size: 0.9rem; color: #7f8c8d;">预期: ${news.expected}</div>` : ''}
                    <div class="date">${news.date}</div>
                </div>
            `).join('');
            
            container.innerHTML = html;
        }
        
        function displayStockPositions(stockPositions) {
            const container = document.getElementById('stockPositions');
            
            if (stockPositions.length === 0) {
                container.innerHTML = '<div class="loading">暂无股票点位数据</div>';
                return;
            }
            
            // 按股票代码分组，取最新的分析
            const latestPositions = {};
            stockPositions.forEach(pos => {
                if (!pos.symbol) return;
                if (!latestPositions[pos.symbol] || pos.date > latestPositions[pos.symbol].date) {
                    latestPositions[pos.symbol] = pos;
                }
            });
            
            const positions = Object.values(latestPositions).slice(0, 15);
            
            const html = `
                <table class="stock-table">
                    <thead>
                        <tr>
                            <th>股票</th>
                            <th>当前价格</th>
                            <th>操作建议</th>
                            <th>支撑位</th>
                            <th>阻力位</th>
                            <th>分析日期</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${positions.map(pos => `
                            <tr>
                                <td>
                                    <strong>${pos.symbol || '-'}</strong><br>
                                    <small style="color: #7f8c8d;">${pos.company_name || '-'}</small>
                                </td>
                                <td>${pos.current_price || '-'}</td>
                                <td>
                                    <span class="action-badge action-${pos.action.toLowerCase().replace('入', 'buy').replace('出', 'sell').replace('有', 'hold').replace('望', 'watch')}">
                                        ${pos.action}
                                    </span>
                                </td>
                                <td class="price-levels">
                                    ${pos.support_levels && pos.support_levels.length > 0 ? 
                                        pos.support_levels.slice(0,2).map(s => `<span class="support">${s}</span>`).join('<br>') : 
                                        '-'
                                    }
                                </td>
                                <td class="price-levels">
                                    ${pos.resistance_levels && pos.resistance_levels.length > 0 ? 
                                        pos.resistance_levels.slice(0,2).map(r => `<span class="resistance">${r}</span>`).join('<br>') : 
                                        '-'
                                    }
                                </td>
                                <td>${pos.date}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            `;
            
            container.innerHTML = html;
        }
        
        function showError(message) {
            document.getElementById('macroNews').innerHTML = `<div class="error">${message}</div>`;
            document.getElementById('stockPositions').innerHTML = `<div class="error">${message}</div>`;
        }
        
        function refreshData() {
            document.getElementById('macroNews').innerHTML = '<div class="loading">正在刷新数据...</div>';
            document.getElementById('stockPositions').innerHTML = '<div class="loading">正在刷新数据...</div>';
            loadData();
        }
        
        // 页面加载完成后自动加载数据
        document.addEventListener('DOMContentLoaded', loadData);
        
        // 自动刷新 (每5分钟)
        setInterval(loadData, 5 * 60 * 1000);
    </script>
</body>
</html>'''
    
    with open(templates_dir / "dashboard.html", 'w', encoding='utf-8') as f:
        f.write(dashboard_html)
    
    print(f"📄 模板文件已创建: {templates_dir}/dashboard.html")


def main():
    """启动Web仪表板"""
    import argparse
    
    parser = argparse.ArgumentParser(description="🌐 财经分析Web仪表板")
    parser.add_argument('--data-dir', help='数据目录路径')
    parser.add_argument('--host', default='0.0.0.0', help='服务器地址 (默认: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=5000, help='端口号 (默认: 5000)')
    parser.add_argument('--debug', action='store_true', help='启用调试模式')
    parser.add_argument('--create-templates', action='store_true', help='创建模板文件')
    
    args = parser.parse_args()
    
    if args.create_templates:
        create_templates()
        return
    
    if not FLASK_AVAILABLE:
        print("❌ Flask未安装，请运行以下命令安装:")
        print("   pip install flask")
        return
    
    print("🌐 财经分析Web仪表板")
    print("=" * 40)
    
    # 确保模板文件存在
    templates_dir = Path.cwd() / "templates"
    if not (templates_dir / "dashboard.html").exists():
        print("📄 创建模板文件...")
        create_templates()
    
    # 启动仪表板
    dashboard = FinanceDashboard(args.data_dir, args.debug)
    dashboard.run(args.host, args.port)


if __name__ == "__main__":
    main()
