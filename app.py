from nicegui import ui
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ┌──────────────────────────────────────────────────────────────────────────────┐
# │ 1. DATA LOADING: 全局只读数据初始化                                           │
# │ ★ 所有原始数据在模块加载时一次性读入，作为只读全局变量                        │
# │ ★ 1000 个用户共享同一份基础数据，节省内存                                     │
# │ ★ 每个用户操作的是 df_global.copy() 的副本，安全隔离                          │
# └──────────────────────────────────────────────────────────────────────────────┘

# 加载订单明细与主表
df_details = pd.read_csv('Details.csv')
df_orders = pd.read_csv('Orders.csv')

# 合并为宽表（星型模型）
df_global = pd.merge(df_details, df_orders, on="Order ID", how="inner")

# 数据清洗：去除分类字段首尾空格
for col in ["Sub-Category", "Category"]:
    if col in df_global.columns:
        df_global[col] = df_global[col].astype(str).str.strip()


# ┌──────────────────────────────────────────────────────────────────────────────┐
# │ 2. SALES DASHBOARD CLASS: 每用户独享实例                                       │
# │ ★ 状态、UI、逻辑、事件全部封装                                               │
# │ ★ 完全支持交叉筛选 + 点击高亮 + 重置 + 多用户安全                            │
# └──────────────────────────────────────────────────────────────────────────────┘

class SalesDashboard:
    def __init__(self):
        # 状态：每个实例维护独立的筛选字典
        self.filters = {}  # e.g., {'State': 'California', 'Sub-Category': 'Chairs'}

        # UI 元素占位（将在 build() 中绑定）
        self.kpi_amount = None
        self.kpi_profit = None
        self.kpi_quantity = None
        self.kpi_orders = None

        self.chart1 = None  # Sub-Category Profit
        self.chart2 = None  # Top States
        self.chart3 = None  # Top Customers

        self.filter_container = None  # 顶部筛选标签容器

    def get_filtered_df(self, exclude_col=None):
        """
        根据 self.filters 返回筛选后的数据副本。
        exclude_col: 渲染某图表时，忽略该列的筛选（实现交叉上下文）。
        """
        d = df_global.copy()
        for col, val in self.filters.items():
            if col == exclude_col:
                continue
            d = d[d[col] == val]
        return d

    def refresh_dashboard(self):
        """统一刷新所有 KPI 与图表"""
        # ── 更新顶部筛选标签 ────────────────────────────────────────────────
        self.filter_container.clear()
        if self.filters:
            with self.filter_container:
                ui.label('Filters: ').classes('text-gray-600 font-bold mr-2')
                for k, v in self.filters.items():
                    ui.label(f'{k}: {v}').classes('filter-tag')
                ui.button('Reset Filters', on_click=self.reset_filters, icon='close') \
                    .props('flat dense color=red size=sm')

        # ── 更新 KPI（应用全部筛选）──────────────────────────────────────────
        df_kpi = self.get_filtered_df(exclude_col=None)
        total_amount = df_kpi['Amount'].sum()
        total_profit = df_kpi['Profit'].sum()
        total_quantity = df_kpi['Quantity'].sum()
        total_orders = df_kpi['Order ID'].nunique()

        self.kpi_amount.set_text(f'${total_amount:,.0f}')
        self.kpi_profit.set_text(f'${total_profit:,.0f}')
        self.kpi_quantity.set_text(f'{total_quantity:,}')
        self.kpi_orders.set_text(f'{total_orders:,}')

        # ── 更新 Chart 1: Profit by Sub-Category ─────────────────────────────
        df_c1 = self.get_filtered_df(exclude_col='Sub-Category')
        df_agg1 = df_c1.groupby('Sub-Category')['Profit'].sum().reset_index()
        df_agg1 = df_agg1.sort_values('Profit', ascending=False)

        selected = self.filters.get('Sub-Category')
        colors = ['#3b82f6' if (not selected or x == selected) else '#dbeafe' for x in df_agg1['Sub-Category']]

        fig1 = px.bar(df_agg1, x='Sub-Category', y='Profit', title='Profit by Sub-Category', template='plotly_white')
        fig1.update_layout(margin=dict(l=20, r=20, t=40, b=20), paper_bgcolor='rgba(0,0,0,0)', clickmode='event+select')
        fig1.update_traces(marker_color=colors)
        self.chart1.update_figure(fig1)

        # ── 更新 Chart 2: Top States by Sales ─────────────────────────────────
        df_c2 = self.get_filtered_df(exclude_col='State')
        df_agg2 = df_c2.groupby('State')['Amount'].sum().reset_index()
        df_agg2 = df_agg2.sort_values('Amount', ascending=False).head(10)

        selected = self.filters.get('State')
        colors = ['#3b82f6' if (not selected or x == selected) else '#dbeafe' for x in df_agg2['State']]

        fig2 = px.bar(df_agg2, x='State', y='Amount', title='Top States by Sales', template='plotly_white')
        fig2.update_layout(margin=dict(l=20, r=20, t=40, b=20), paper_bgcolor='rgba(0,0,0,0)', clickmode='event+select')
        fig2.update_traces(marker_color=colors)
        self.chart2.update_figure(fig2)

        # ── 更新 Chart 3: Top Customers by Sales ──────────────────────────────
        df_c3 = self.get_filtered_df(exclude_col='CustomerName')
        df_agg3 = df_c3.groupby('CustomerName')['Amount'].sum().reset_index()
        df_agg3 = df_agg3.sort_values('Amount', ascending=False).head(10)

        selected = self.filters.get('CustomerName')
        colors = ['#10b981' if (not selected or x == selected) else '#d1fae5' for x in df_agg3['CustomerName']]

        fig3 = px.bar(df_agg3, x='CustomerName', y='Amount', title='Top Customers by Sales', template='plotly_white')
        fig3.update_layout(margin=dict(l=20, r=20, t=40, b=20), paper_bgcolor='rgba(0,0,0,0)', clickmode='event+select')
        fig3.update_traces(marker_color=colors)
        self.chart3.update_figure(fig3)

    def reset_filters(self):
        """清空所有筛选并刷新"""
        self.filters.clear()
        ui.notify('Filters reset', type='positive')
        self.refresh_dashboard()

    def handle_click(self, event, column_name):
        """通用点击处理器：切换筛选状态"""
        if 'points' in event.args and len(event.args['points']) > 0:
            click_val = event.args['points'][0]['x']

            # 切换逻辑：已选中则取消，否则设置
            if self.filters.get(column_name) == click_val:
                self.filters.pop(column_name)
                ui.notify(f'Removed filter: {column_name}', type='info')
            else:
                self.filters[column_name] = click_val
                ui.notify(f'Filtered by {column_name}: {click_val}', type='info')

            self.refresh_dashboard()

    def build(self):
        # ── 注入 CSS ───────────────────────────────────────────────────────
        ui.add_head_html('''
            <style>
                .kpi-card { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border-radius: 8px; padding: 16px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
                .kpi-title { font-size: 0.9rem; opacity: 0.9; }
                .kpi-value { font-size: 1.8rem; font-weight: bold; margin-top: 4px; }
                .chart-card { border-radius: 8px; padding: 4px; background: white; box-shadow: 0 2px 4px rgba(0,0,0,0.05); border: 1px solid #eee; }
                .filter-tag { background-color: #e0f2fe; color: #0369a1; padding: 4px 12px; border-radius: 16px; font-size: 0.85rem; display: flex; align-items: center; gap: 8px; }
            </style>
        ''')

        # ── 标题与筛选容器 ─────────────────────────────────────────────────
        with ui.column().classes('w-full items-left mb-6'):
            ui.label('📊 Sales Overview').classes('text-2xl font-bold text-center mb-6 text-gray-800')
            self.filter_container = ui.row().classes('items-center gap-2 min-h-[40px]')

        # ── KPI 行 ─────────────────────────────────────────────────────────
        with ui.row().classes('w-full justify-between gap-4 px-10 mb-8'):
            with ui.card().classes('kpi-card flex-1'):
                ui.label('Total Amount').classes('kpi-title')
                self.kpi_amount = ui.label('$0').classes('kpi-value')
            with ui.card().classes('kpi-card flex-1'):
                ui.label('Total Profit').classes('kpi-title')
                self.kpi_profit = ui.label('$0').classes('kpi-value')
            with ui.card().classes('kpi-card flex-1'):
                ui.label('Total Quantity').classes('kpi-title')
                self.kpi_quantity = ui.label('0').classes('kpi-value')
            with ui.card().classes('kpi-card flex-1'):
                ui.label('Order Count').classes('kpi-title')
                self.kpi_orders = ui.label('0').classes('kpi-value')

        # ── 图表行 ─────────────────────────────────────────────────────────
        with ui.row().classes('w-full justify-between gap-4 px-10'):
            with ui.card().classes('chart-card flex-1'):
                self.chart1 = ui.plotly(go.Figure()).classes('w-full h-80')
                self.chart1.on('plotly_click', lambda e: self.handle_click(e, 'Sub-Category'))

            with ui.card().classes('chart-card flex-1'):
                self.chart2 = ui.plotly(go.Figure()).classes('w-full h-80')
                self.chart2.on('plotly_click', lambda e: self.handle_click(e, 'State'))

            with ui.card().classes('chart-card flex-1'):
                self.chart3 = ui.plotly(go.Figure()).classes('w-full h-80')
                self.chart3.on('plotly_click', lambda e: self.handle_click(e, 'CustomerName'))

        # 初始化仪表板
        self.refresh_dashboard()


# ┌──────────────────────────────────────────────────────────────────────────────┐
# │ 3. ENTRY POINT: 每用户独立实例化                                              │
# │ ★ @ui.page('/') 每次调用 index() 都创建全新 SalesDashboard()                 │
# └──────────────────────────────────────────────────────────────────────────────┘

@ui.page('/')
def index():
    dashboard = SalesDashboard()
    dashboard.build()


# 启动应用
ui.run(title='Sales Dashboard', port=8081)