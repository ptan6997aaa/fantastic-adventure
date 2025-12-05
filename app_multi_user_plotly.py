from nicegui import ui
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ┌──────────────────────────────────────────────────────────────────────────────┐
# │ 1. DATA LOADING: 全局只读数据初始化                                          │
# │ ──────────────────────────────────────────────────────────────────────────── │
# │ - 此处代码在服务器启动时仅运行一次。                                         │
# │ - 1000个用户共享同一份 df_global 内存，极大节省资源。                        │
# └──────────────────────────────────────────────────────────────────────────────┘
df_details = pd.read_csv('Details.csv')
df_orders = pd.read_csv('Orders.csv')
df_global = pd.merge(df_details, df_orders, on="Order ID", how="inner")


# 数据清洗（全局统一处理）
if "Sub-Category" in df_global.columns:
    df_global["Sub-Category"] = df_global["Sub-Category"].astype(str).str.strip()
if "Category" in df_global.columns:
    df_global["Category"] = df_global["Category"].astype(str).str.strip()

# ┌──────────────────────────────────────────────────────────────────────────────┐
# │ 2. DASHBOARD CLASS: 核心交互式仪表板类                                       │
# │ ──────────────────────────────────────────────────────────────────────────── │
# │ - 每个浏览器 Tab 页对应一个独立的 Dashboard 实例。                             │
# │ - self.state 存储当前用户的筛选条件。                                        │
# └──────────────────────────────────────────────────────────────────────────────┘

class Dashboard:
    def __init__(self):
        # ── 状态管理 ──
        # 使用 'All' 代表未筛选
        self.state = {
            'Sub-Category': 'All',
            'State': 'All',
            'CustomerName': 'All'
        }

        # ── UI 组件引用 (占位符) ──
        self.filter_container = None
        self.kpi_amount = None
        self.kpi_profit = None
        self.kpi_quantity = None
        self.kpi_orders = None
        
        self.chart_subcat = None
        self.chart_state = None
        self.chart_customer = None

    # ── 数据核心：智能筛选引擎 ──────────────────────────────────────────────────
    def get_data(self, ignore_subcat=False, ignore_state=False, ignore_customer=False):
        """
        根据 self.state 返回筛选后的数据副本。
        参数 ignore_xxx 用于 Cross-Filtering（交叉筛选）：
        例如：渲染“州”图表时，应该忽略“州”的筛选条件，以便用户能看到其他州的柱子（非选中状态）。
        """
        d = df_global.copy()

        # 1. 应用 Sub-Category 筛选
        if not ignore_subcat and self.state['Sub-Category'] != 'All':
            d = d[d['Sub-Category'] == self.state['Sub-Category']]
        
        # 2. 应用 State 筛选
        if not ignore_state and self.state['State'] != 'All':
            d = d[d['State'] == self.state['State']]

        # 3. 应用 CustomerName 筛选
        if not ignore_customer and self.state['CustomerName'] != 'All':
            d = d[d['CustomerName'] == self.state['CustomerName']]

        return d

    # ── 渲染器：顶部状态标签 ────────────────────────────────────────────────────
    def render_filters_label(self):
        self.filter_container.clear()
        active_filters = [f"{k}: {v}" for k, v in self.state.items() if v != 'All']
        
        with self.filter_container:
            if not active_filters:
                ui.label('No Active Filters').classes('text-gray-400 italic')
            else:
                ui.label('Filters: ').classes('text-gray-600 font-bold mr-2')
                for f in active_filters:
                    ui.label(f).classes('bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-xs')
                # 重置按钮
                ui.button('Reset', on_click=self.reset_filters, icon='close').props('flat dense color=red size=sm ml-2')

    # ── 渲染器：KPI 卡片 ────────────────────────────────────────────────────────
    def render_kpis(self):
        # KPI 需要应用所有筛选条件
        d = self.get_data()
        
        if d.empty:
            self.kpi_amount.set_text('$0')
            self.kpi_profit.set_text('$0')
            self.kpi_quantity.set_text('0')
            self.kpi_orders.set_text('0')
            return

        self.kpi_amount.set_text(f"${d['Amount'].sum():,.0f}")
        self.kpi_profit.set_text(f"${d['Profit'].sum():,.0f}")
        self.kpi_quantity.set_text(f"{d['Quantity'].sum():,}")
        self.kpi_orders.set_text(f"{d['Order ID'].nunique():,}")

    # ── 渲染器：通用图表逻辑 ────────────────────────────────────────────────────
    def _update_bar_chart(self, chart_element, data_func, group_col, value_col, title, color_hex):
        """
        通用辅助函数，用于绘制带有高亮逻辑的柱状图
        """
        # 1. 获取数据（忽略自身的筛选，以显示完整上下文）
        d = data_func() 
        
        if d.empty:
            chart_element.update_figure(go.Figure())
            return

        # 2. 聚合排序
        df_agg = d.groupby(group_col)[value_col].sum().reset_index().sort_values(value_col, ascending=False).head(10)
        
        # 3. 计算颜色（高亮选中项）
        current_selection = self.state[group_col]
        # 逻辑：如果没有选中，全深色；如果选中了某项，该项深色，其他浅色
        colors = [
            color_hex if (current_selection == 'All' or x == current_selection) else '#e2e8f0' 
            for x in df_agg[group_col]
        ]

        # 4. 绘图
        fig = px.bar(df_agg, x=group_col, y=value_col, title=title, template='plotly_white')
        fig.update_layout(
            margin=dict(l=20, r=20, t=40, b=20), 
            paper_bgcolor='rgba(0,0,0,0)', 
            clickmode='event+select'
        )
        fig.update_traces(marker_color=colors)
        chart_element.update_figure(fig)

    # ── 渲染器：具体图表调用 ────────────────────────────────────────────────────
    def render_charts(self):
        # 1. Sub-Category 图表 (忽略 Sub-Category 筛选)
        self._update_bar_chart(
            chart_element=self.chart_subcat,
            data_func=lambda: self.get_data(ignore_subcat=True),
            group_col='Sub-Category',
            value_col='Profit',
            title='Profit by Sub-Category',
            color_hex='#3b82f6' # Blue
        )

        # 2. State 图表 (忽略 State 筛选)
        self._update_bar_chart(
            chart_element=self.chart_state,
            data_func=lambda: self.get_data(ignore_state=True),
            group_col='State',
            value_col='Amount',
            title='Top 10 States by Sales',
            color_hex='#8b5cf6' # Purple
        )

        # 3. Customer 图表 (忽略 CustomerName 筛选)
        self._update_bar_chart(
            chart_element=self.chart_customer,
            data_func=lambda: self.get_data(ignore_customer=True),
            group_col='CustomerName',
            value_col='Amount',
            title='Top 10 Customers by Sales',
            color_hex='#10b981' # Green
        )

    # ── 主刷新入口 ──────────────────────────────────────────────────────────────
    def update_dashboard(self):
        self.render_filters_label()
        self.render_kpis()
        self.render_charts()

    # ── 事件处理 ────────────────────────────────────────────────────────────────
    def reset_filters(self):
        self.state = {k: 'All' for k in self.state}
        ui.notify('Filters reset', type='positive')
        self.update_dashboard()

    def handle_click(self, event, col_name):
        """通用点击处理函数"""
        if event.args and 'points' in event.args and len(event.args['points']) > 0:
            clicked_val = event.args['points'][0]['x']
            
            # 切换逻辑：点击已选中的则取消，否则选中
            if self.state[col_name] == clicked_val:
                self.state[col_name] = 'All'
                ui.notify(f'Removed filter: {col_name}', type='info')
            else:
                self.state[col_name] = clicked_val
                ui.notify(f'Filtered by {col_name}: {clicked_val}', type='info')
            
            self.update_dashboard()

    # ── UI 构建 ────────────────────────────────────────────────────────────────
    def build(self):
        # 自定义 CSS
        ui.add_head_html('''
            <style>
                .kpi-card { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border-radius: 8px; padding: 16px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
                .kpi-title { font-size: 0.9rem; opacity: 0.9; }
                .kpi-value { font-size: 1.8rem; font-weight: bold; margin-top: 4px; }
                .chart-card { border-radius: 8px; padding: 4px; background: white; box-shadow: 0 2px 4px rgba(0,0,0,0.05); border: 1px solid #eee; }
            </style>
        ''')

        # 1. 标题头
        with ui.column().classes('w-full mb-6'):
            ui.label('📊 Sales Overview Dashboard').classes('text-2xl font-bold text-gray-800')
            # 筛选标签容器
            self.filter_container = ui.row().classes('items-center gap-2 min-h-[32px]')

        # 2. KPI 行
        with ui.row().classes('w-full justify-between gap-4 mb-8'):
            with ui.card().classes('kpi-card flex-1'):
                ui.label('Total Amount').classes('kpi-title')
                self.kpi_amount = ui.label().classes('kpi-value')
            
            with ui.card().classes('kpi-card flex-1'):
                ui.label('Total Profit').classes('kpi-title')
                self.kpi_profit = ui.label().classes('kpi-value')

            with ui.card().classes('kpi-card flex-1'):
                ui.label('Total Quantity').classes('kpi-title')
                self.kpi_quantity = ui.label().classes('kpi-value')

            with ui.card().classes('kpi-card flex-1'):
                ui.label('Order Count').classes('kpi-title')
                self.kpi_orders = ui.label().classes('kpi-value')

        # 3. 图表行
        with ui.row().classes('w-full justify-between gap-4'):
            # Chart 1: Sub-Category
            with ui.card().classes('chart-card flex-1'):
                self.chart_subcat = ui.plotly({}).classes('w-full h-80')
                self.chart_subcat.on('plotly_click', lambda e: self.handle_click(e, 'Sub-Category'))
            
            # Chart 2: State
            with ui.card().classes('chart-card flex-1'):
                self.chart_state = ui.plotly({}).classes('w-full h-80')
                self.chart_state.on('plotly_click', lambda e: self.handle_click(e, 'State'))

            # Chart 3: Customer
            with ui.card().classes('chart-card flex-1'):
                self.chart_customer = ui.plotly({}).classes('w-full h-80')
                self.chart_customer.on('plotly_click', lambda e: self.handle_click(e, 'CustomerName'))

        # 初始化首次渲染
        self.update_dashboard()

# ┌──────────────────────────────────────────────────────────────────────────────┐
# │ 3. ENTRY POINT: 页面入口                                                     │
# │ ──────────────────────────────────────────────────────────────────────────── │
# └──────────────────────────────────────────────────────────────────────────────┘

@ui.page('/')
def index():
    # 为每个新连接创建一个独立的 Dashboard 实例
    dashboard = Dashboard()
    dashboard.build()

ui.run(title='Sales Dashboard Best Practice', port=8081)