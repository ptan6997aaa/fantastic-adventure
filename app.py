from nicegui import ui
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

# ┌──────────────────────────────────────────────────────────────────────────────┐
# │ 1. DATA LOADING: 数据加载层                                                  │
# │ ---------------------------------------------------------------------------- │
# │ 目前使用模拟数据。等你有了 CSV 文件后，请修改这里的代码。                    │
# └──────────────────────────────────────────────────────────────────────────────┘

def load_data():
    """
    加载数据的函数。
    TODO: 实际使用时，请替换为 pd.read_csv('your_file.csv')
    """
    # --- 模拟数据生成开始 ---
    np.random.seed(42)
    dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
    categories = ['Electronics', 'Clothing', 'Home', 'Beauty']
    regions = ['North', 'South', 'East', 'West']
    
    data = {
        'Date': np.random.choice(dates, 500),
        'Category': np.random.choice(categories, 500),
        'Region': np.random.choice(regions, 500),
        'Sales': np.random.randint(100, 1000, 500),
        'Profit': np.random.randint(10, 200, 500),
        'Quantity': np.random.randint(1, 10, 500)
    }
    df = pd.DataFrame(data)
    # 增加一个月份列用于分析
    df['Month'] = df['Date'].dt.strftime('%Y-%m')
    return df
    # --- 模拟数据生成结束 ---

# 初始化全局只读数据
df_global = load_data()


# ┌──────────────────────────────────────────────────────────────────────────────┐
# │ 2. DASHBOARD CLASS: 业务逻辑与 UI 层                                         │
# └──────────────────────────────────────────────────────────────────────────────┘

class Dashboard:
    def __init__(self):
        # ── 状态管理 ──
        # 记录当前的筛选条件，'All' 代表不过滤
        self.state = {
            'category': 'All',
            'region': 'All',
            'month': 'All'
        }

        # ── UI 占位符 ──
        # KPI 标签
        self.kpi_sales = None
        self.kpi_profit = None
        self.kpi_orders = None
        self.kpi_margin = None
        
        # 图表对象
        self.chart_trend = None   # 图表1：趋势
        self.chart_cat = None     # 图表2：分类
        self.chart_region = None  # 图表3：地区
        
        # 顶部状态文本
        self.filter_label = None

    # ── 数据过滤核心逻辑 ──
    def get_data(self, ignore_category=False, ignore_region=False, ignore_month=False):
        """
        根据 self.state 筛选数据。
        ignore_xxx 参数用于在绘制某维度图表时，忽略该维度的筛选，以显示完整分布。
        """
        d = df_global.copy()

        # 筛选：Category
        if not ignore_category and self.state['category'] != 'All':
            d = d[d['Category'] == self.state['category']]
        
        # 筛选：Region
        if not ignore_region and self.state['region'] != 'All':
            d = d[d['Region'] == self.state['region']]

        # 筛选：Month
        if not ignore_month and self.state['month'] != 'All':
            d = d[d['Month'] == self.state['month']]
            
        return d

    # ── 渲染 KPI (一行四个) ──
    def render_kpis(self):
        d = self.get_data() # 获取应用了所有筛选的数据

        if d.empty:
            self.kpi_sales.set_text("0")
            self.kpi_profit.set_text("0")
            self.kpi_orders.set_text("0")
            self.kpi_margin.set_text("0%")
            return

        # 1. 总销售额
        total_sales = d['Sales'].sum()
        self.kpi_sales.set_text(f"${total_sales:,.0f}")

        # 2. 总利润
        total_profit = d['Profit'].sum()
        self.kpi_profit.set_text(f"${total_profit:,.0f}")

        # 3. 订单数 (行数)
        total_orders = len(d)
        self.kpi_orders.set_text(f"{total_orders:,}")

        # 4. 利润率 (Profit / Sales)
        margin = (total_profit / total_sales * 100) if total_sales > 0 else 0
        self.kpi_margin.set_text(f"{margin:.1f}%")

    # ── 渲染图表 (一行三个) ──
    def render_charts(self):
        self.render_chart_trend()
        self.render_chart_category()
        self.render_chart_region()

    def render_chart_trend(self):
        """图表 1: 时间趋势 (按月)"""
        # 忽略月份筛选，这样用户点击某个月份时，依然能看到整体趋势
        d = self.get_data(ignore_month=True) 
        
        if d.empty:
            self.chart_trend.update_figure(go.Figure())
            return

        df_gb = d.groupby('Month')['Sales'].sum().reset_index().sort_values('Month')
        
        fig = px.bar(df_gb, x='Month', y='Sales', title='Monthly Sales Trend')
        
        # 高亮选中的月份
        colors = ['#6366f1'] * len(df_gb) # 默认靛蓝色
        if self.state['month'] != 'All':
            colors = ['#ef4444' if m == self.state['month'] else '#c7c7c7' for m in df_gb['Month']]
        
        fig.update_traces(marker_color=colors)
        fig.update_layout(margin=dict(l=20, r=20, t=40, b=20), paper_bgcolor='rgba(0,0,0,0)')
        self.chart_trend.update_figure(fig)

    def render_chart_category(self):
        """图表 2: 按分类 (Category)"""
        d = self.get_data(ignore_category=True) # 忽略自身维度筛选
        
        if d.empty:
            self.chart_cat.update_figure(go.Figure())
            return

        df_gb = d.groupby('Category')['Sales'].sum().reset_index().sort_values('Sales', ascending=False)
        
        fig = px.bar(df_gb, x='Category', y='Sales', title='Sales by Category')
        
        # 高亮选中项
        colors = ['#10b981'] * len(df_gb) # 默认绿色
        if self.state['category'] != 'All':
            colors = ['#ef4444' if c == self.state['category'] else '#c7c7c7' for c in df_gb['Category']]

        fig.update_traces(marker_color=colors)
        fig.update_layout(margin=dict(l=20, r=20, t=40, b=20), paper_bgcolor='rgba(0,0,0,0)')
        self.chart_cat.update_figure(fig)

    def render_chart_region(self):
        """图表 3: 按地区 (Region)"""
        d = self.get_data(ignore_region=True) # 忽略自身维度筛选
        
        if d.empty:
            self.chart_region.update_figure(go.Figure())
            return

        df_gb = d.groupby('Region')['Sales'].sum().reset_index().sort_values('Sales', ascending=False)
        
        fig = px.bar(df_gb, x='Region', y='Sales', title='Sales by Region')
        
        # 高亮选中项
        colors = ['#f59e0b'] * len(df_gb) # 默认琥珀色
        if self.state['region'] != 'All':
            colors = ['#ef4444' if r == self.state['region'] else '#c7c7c7' for r in df_gb['Region']]

        fig.update_traces(marker_color=colors)
        fig.update_layout(margin=dict(l=20, r=20, t=40, b=20), paper_bgcolor='rgba(0,0,0,0)')
        self.chart_region.update_figure(fig)

    # ── 交互事件处理 ──
    def update_all(self):
        """统一刷新界面"""
        # 更新文字提示
        filters = [f"{k}:{v}" for k,v in self.state.items() if v != 'All']
        filter_text = " | ".join(filters) if filters else "None"
        self.filter_label.set_text(f"Current Filters: {filter_text}")
        
        self.render_kpis()
        self.render_charts()

    def reset_filters(self):
        self.state = {'category': 'All', 'region': 'All', 'month': 'All'}
        self.update_all()

    def handle_click_trend(self, e):
        if e.args and 'points' in e.args:
            click_val = e.args['points'][0]['x']
            # 点击已选中的则取消，否则选中
            self.state['month'] = 'All' if self.state['month'] == click_val else click_val
            self.update_all()

    def handle_click_cat(self, e):
        if e.args and 'points' in e.args:
            click_val = e.args['points'][0]['x']
            self.state['category'] = 'All' if self.state['category'] == click_val else click_val
            self.update_all()

    def handle_click_region(self, e):
        if e.args and 'points' in e.args:
            click_val = e.args['points'][0]['x']
            self.state['region'] = 'All' if self.state['region'] == click_val else click_val
            self.update_all()

    # ── UI 构建 ──
    def build(self):
        # 样式注入
        ui.add_head_html('''
            <style>
                .kpi-card { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border-radius: 8px; padding: 16px; }
                .kpi-title { font-size: 0.9rem; opacity: 0.9; }
                .kpi-value { font-size: 1.8rem; font-weight: bold; margin-top: 4px; }
                .chart-card { border-radius: 8px; border: 1px solid #e5e7eb; padding: 4px; box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05); }
            </style>
        ''')

        # 1. 顶部 Header
        with ui.row().classes('w-full items-center justify-between mb-6'):
            with ui.column().classes('gap-0'):
                ui.label('Business Sales Dashboard').classes('text-2xl font-bold text-gray-800')
                self.filter_label = ui.label('Current Filters: None').classes('text-sm text-gray-500')
            
            ui.button('Reset Filters', icon='refresh', on_click=self.reset_filters).classes('bg-gray-700 text-white')

        # 2. KPI 行 (一行 4 列)
        with ui.grid(columns=4).classes('w-full gap-4 mb-6'):
            # KPI 1
            with ui.card().classes('kpi-card'):
                ui.label('Total Sales').classes('kpi-title')
                self.kpi_sales = ui.label('$0').classes('kpi-value')
            # KPI 2
            with ui.card().classes('kpi-card'):
                ui.label('Total Profit').classes('kpi-title')
                self.kpi_profit = ui.label('$0').classes('kpi-value')
            # KPI 3
            with ui.card().classes('kpi-card'):
                ui.label('Transactions').classes('kpi-title')
                self.kpi_orders = ui.label('0').classes('kpi-value')
            # KPI 4
            with ui.card().classes('kpi-card'):
                ui.label('Profit Margin').classes('kpi-title')
                self.kpi_margin = ui.label('0%').classes('kpi-value')

        # 3. 图表行 (一行 3 列)
        with ui.grid(columns=3).classes('w-full gap-4'):
            
            # Chart 1: Month Trend
            with ui.card().classes('chart-card w-full h-80'):
                self.chart_trend = ui.plotly({}).classes('w-full h-full')
                self.chart_trend.on('plotly_click', self.handle_click_trend)
            
            # Chart 2: By Category
            with ui.card().classes('chart-card w-full h-80'):
                self.chart_cat = ui.plotly({}).classes('w-full h-full')
                self.chart_cat.on('plotly_click', self.handle_click_cat)
            
            # Chart 3: By Region
            with ui.card().classes('chart-card w-full h-80'):
                self.chart_region = ui.plotly({}).classes('w-full h-full')
                self.chart_region.on('plotly_click', self.handle_click_region)

        # 初始化渲染
        self.update_all()

# ┌──────────────────────────────────────────────────────────────────────────────┐
# │ 3. APP ENTRY: 入口                                                           │
# └──────────────────────────────────────────────────────────────────────────────┘

@ui.page('/')
def index():
    # 实例化 Dashboard，每个用户独立
    dash = Dashboard()
    dash.build()

ui.run(title="Sales Dashboard", port=8080)