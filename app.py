from nicegui import ui
import pandas as pd

# ┌──────────────────────────────────────────────────────────────────────────────┐
# │ 1. DATA LOADING: 全局只读数据初始化 (只执行一次)                             │
# │ ──────────────────────────────────────────────────────────────────────────── │
# │ ★ 关键设计：                                                                 │
# │   - 模拟 "单例模式"，数据常驻内存，避免每个用户刷新页面都重新读取 CSV          │
# │   - 所有 Dashboard 实例共享这份数据，但只能读取，不能修改                    │
# └──────────────────────────────────────────────────────────────────────────────┘

# 模拟数据加载（为了确保代码可运行，这里增加了容错，您保留原有的读取逻辑即可）
try:
    df_details = pd.read_csv('Details.csv')
    df_orders = pd.read_csv('Orders.csv')
    # 预处理：合并与清洗
    df_global = pd.merge(df_details, df_orders, on="Order ID", how="inner")
    
    # 统一清洗字符串列，避免后续报错
    for col in ["Sub-Category", "Category", "State", "CustomerName"]:
        if col in df_global.columns:
            df_global[col] = df_global[col].astype(str).str.strip()
            
    print(f"Data Loaded Successfully: {len(df_global)} rows")
except Exception as e:
    print(f"Data Load Warning: {e}. Using dummy data for demonstration.")
    # 兜底模拟数据，方便直接运行测试
    df_global = pd.DataFrame({
        'Order ID': [f'Ord-{i}' for i in range(100)],
        'Sub-Category': ['Phones', 'Chairs', 'Tables', 'Storage'] * 25,
        'State': ['Texas', 'California', 'New York', 'Florida'] * 25,
        'CustomerName': [f'User-{i%10}' for i in range(100)],
        'Amount': [i * 10 for i in range(100)],
        'Profit': [i * 2 for i in range(100)],
        'Quantity': [i % 5 + 1 for i in range(100)]
    })

# ── 辅助函数：ECharts 配置构建器 (纯逻辑，无状态，可放在类外) ────────────────────
def build_bar_chart_option(title, x_data, y_data, highlight_val=None, base_color='#3b82f6'):
    """构建 ECharts Option 字典"""
    series_data = []
    color_selected = base_color
    color_unselected = '#cbd5e1'  # 未选中时的浅灰色
    
    for x, y in zip(x_data, y_data):
        # 逻辑：如果没有筛选，或者当前项就是筛选项，则高亮
        is_highlighted = (highlight_val is None) or (x == highlight_val)
        current_color = color_selected if is_highlighted else color_unselected
        series_data.append({'value': y, 'itemStyle': {'color': current_color}})

    return {
        'title': {'text': title, 'left': 'center', 'top': '5%', 'textStyle': {'fontSize': 14, 'color': '#333'}},
        'tooltip': {'trigger': 'axis', 'axisPointer': {'type': 'shadow'}},
        'grid': {'left': '3%', 'right': '4%', 'bottom': '10%', 'containLabel': True},
        'xAxis': [{
            'type': 'category',
            'data': x_data,
            'axisTick': {'alignWithLabel': True},
            'axisLabel': {'rotate': 45, 'interval': 0, 'fontSize': 10}
        }],
        'yAxis': [{'type': 'value'}],
        'series': [{'type': 'bar', 'barWidth': '60%', 'data': series_data}]
    }

# ┌──────────────────────────────────────────────────────────────────────────────┐
# │ 2. DASHBOARD CLASS: 核心交互式仪表板类                                       │
# │ ──────────────────────────────────────────────────────────────────────────── │
# │ ★ 架构优势：每个用户 session 拥有一个独立的 Dashboard 实例                   │
# └──────────────────────────────────────────────────────────────────────────────┘

class Dashboard:
    def __init__(self):
        # ── 状态管理：每个实例维护独立的筛选字典 ──────────────────────────────────
        # 结构示例: {'State': 'Texas', 'Sub-Category': 'Phones'}
        self.filters = {} 
        
        # ── UI 引用：占位符，build() 时绑定 ──────────────────────────────────────
        self.kpi_labels = {}     # 存储 KPI 的 label 组件引用
        self.chart_sub = None    # 子类别图表引用
        self.chart_state = None  # 州分布图表引用
        self.chart_cust = None   # 客户图表引用
        self.filter_container = None # 顶部筛选标签容器

    # ── 数据过滤核心 ──────────────────────────────────────────────────────────
    def get_data(self, ignore_col=None):
        """
        根据 self.filters 过滤全局数据 df_global，返回副本。
        ignore_col: 渲染自身图表时，忽略自身的筛选条件 (实现 Cross-Filtering 效果)
        """
        d = df_global.copy()
        
        for col, val in self.filters.items():
            if col == ignore_col: 
                continue # 如果是渲染 'State' 图表，就不要把 'State=Texas' 的筛选加进去，否则只能看到一根柱子
            d = d[d[col] == val]
            
        return d

    # ── KPI 渲染 ─────────────────────────────────────────────────────────────
    def render_kpis(self):
        d = self.get_data() # KPI 受所有筛选器影响，不需要 ignore
        
        # 安全计算，防止空数据报错
        total_amt = d['Amount'].sum() if not d.empty else 0
        total_prf = d['Profit'].sum() if not d.empty else 0
        total_qty = d['Quantity'].sum() if not d.empty else 0
        total_ord = d['Order ID'].nunique() if not d.empty else 0

        self.kpi_labels['amt'].set_text(f"${total_amt:,.0f}")
        self.kpi_labels['prf'].set_text(f"${total_prf:,.0f}")
        self.kpi_labels['qty'].set_text(f"{total_qty:,}")
        self.kpi_labels['ord'].set_text(f"{total_ord:,}")

    # ── 顶部筛选标签渲染 ──────────────────────────────────────────────────────
    def render_filter_tags(self):
        self.filter_container.clear()
        if self.filters:
            with self.filter_container:
                ui.label('Active Filters:').classes('text-gray-500 font-bold text-sm my-auto')
                for k, v in self.filters.items():
                    # 点击标签也可以取消筛选
                    ui.label(f'{k}: {v}').classes(
                        'bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-xs cursor-pointer hover:bg-red-100 hover:text-red-800 transition'
                    ).on('click', lambda _, key=k: self.remove_filter(key)) # 闭包绑定 key
                
                # 清除所有按钮
                ui.button(icon='delete', on_click=self.reset_filters).props('flat dense round color=grey size=sm').tooltip('Clear All')

    # ── 通用图表渲染逻辑 ──────────────────────────────────────────────────────
    def update_chart_component(self, chart_component, col_name, val_col, color, title):
        """
        通用的图表刷新逻辑
        """
        # STEP 1: 获取数据 (ignore_col = col_name)
        d = self.get_data(ignore_col=col_name)
        
        if d.empty:
            # 如果没数据，只更新标题
            chart_component.options['title'] = {'text': f"{title} (No Data)"}
            chart_component.update()
            return

        # STEP 2: 聚合
        df_grp = d.groupby(col_name)[val_col].sum().reset_index().sort_values(val_col, ascending=False)
        # 取前10，避免图表太挤
        df_grp = df_grp.head(10)

        # STEP 3: 构建 Option
        current_filter_val = self.filters.get(col_name)
        
        opt = build_bar_chart_option(
            title=title,
            x_data=df_grp[col_name].tolist(),
            y_data=df_grp[val_col].round(0).tolist(),
            highlight_val=current_filter_val,
            base_color=color
        )
        
        # STEP 4: 更新 UI (修正部分)
        # ECharts 的 options 是只读属性，不能直接用 = 赋值
        # 必须先 clear() 内容，再 update() 新内容
        chart_component.options.clear()
        chart_component.options.update(opt)
        chart_component.update()

    # ── 主更新入口 ───────────────────────────────────────────────────────────
    def update_dashboard(self):
        """调度所有组件刷新"""
        self.render_filter_tags()
        self.render_kpis()
        
        # 刷新三个图表
        self.update_chart_component(self.chart_sub, 'Sub-Category', 'Profit', '#28738a', 'Profit by Sub-Category')
        self.update_chart_component(self.chart_state, 'State', 'Amount', '#3b82f6', 'Sales by State (Top 10)')
        self.update_chart_component(self.chart_cust, 'CustomerName', 'Amount', '#10b981', 'Sales by Customer (Top 10)')

    # ── 事件处理器 ───────────────────────────────────────────────────────────
    def handle_chart_click(self, e, col_name):
        """
        处理 ECharts 点击事件
        e: ECharts 点击事件对象 (NiceGUI 封装)
        col_name: 该图表对应的 DataFrame 列名
        """
        if e.name: # e.name 是点击的柱子名称 (例如 'Texas')
            click_val = e.name
            
            # 逻辑：如果已选中则取消，否则选中
            if self.filters.get(col_name) == click_val:
                self.filters.pop(col_name)
                ui.notify(f'Removed filter: {col_name}')
            else:
                self.filters[col_name] = click_val
                ui.notify(f'Filtered by {col_name}: {click_val}')
            
            self.update_dashboard()

    def remove_filter(self, key):
        if key in self.filters:
            del self.filters[key]
            self.update_dashboard()

    def reset_filters(self):
        self.filters.clear()
        ui.notify('All filters reset')
        self.update_dashboard()

    # ── UI 构建 ─────────────────────────────────────────────────────────────
    def build(self):
        # 样式注入
        ui.add_head_html('''
            <style>
                .kpi-card { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border-radius: 8px; padding: 16px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
                .chart-card { border-radius: 8px; padding: 4px; background: white; box-shadow: 0 2px 4px rgba(0,0,0,0.05); border: 1px solid #eee; } 
            </style>
        ''')

        # 1. 标题与筛选栏
        with ui.column().classes('w-full mb-6'):
            ui.label('📊 Sales Dashboard (Class-Based Architecture)').classes('text-2xl font-bold text-gray-800 px-4 pt-4')
            # 筛选标签容器
            self.filter_container = ui.row().classes('px-4 gap-2 min-h-[32px] items-center')

        # 2. KPI 区域
        kpi_configs = [
            ('amt', 'Total Amount'), 
            ('prf', 'Total Profit'), 
            ('qty', 'Total Quantity'), 
            ('ord', 'Order Count')
        ]
        with ui.row().classes('w-full justify-between gap-4 px-4 mb-6'):
            for key, title in kpi_configs:
                with ui.card().classes('kpi-card flex-1'):
                    ui.label(title).classes('text-sm opacity-80')
                    # 保存引用到 self.kpi_labels 字典
                    self.kpi_labels[key] = ui.label('...').classes('text-2xl font-bold mt-1')

        # 3. 图表区域 (3列布局)
        with ui.row().classes('w-full gap-4 px-4'):
            # Chart 1: Sub-Category
            with ui.card().classes('chart-card flex-1'):
                self.chart_sub = ui.echart({'xAxis': {}, 'yAxis': {}, 'series': []}).classes('w-full h-80')
                # 绑定点击事件，使用 lambda 传递额外的 col_name 参数
                self.chart_sub.on_point_click(lambda e: self.handle_chart_click(e, 'Sub-Category'))

            # Chart 2: State
            with ui.card().classes('chart-card flex-1'):
                self.chart_state = ui.echart({}).classes('w-full h-80')
                self.chart_state.on_point_click(lambda e: self.handle_chart_click(e, 'State'))

            # Chart 3: Customer
            with ui.card().classes('chart-card flex-1'):
                self.chart_cust = ui.echart({}).classes('w-full h-80')
                self.chart_cust.on_point_click(lambda e: self.handle_chart_click(e, 'CustomerName'))

        # 4. 初始化首次渲染
        self.update_dashboard()

# ┌──────────────────────────────────────────────────────────────────────────────┐
# │ 3. ENTRY POINT: 页面入口                                                     │
# │ ──────────────────────────────────────────────────────────────────────────── │
# │ 每次用户访问，都会执行 index() -> 创建新的 Dashboard 实例 -> build() UI      │
# └──────────────────────────────────────────────────────────────────────────────┘

@ui.page('/')
def index():
    dashboard = Dashboard()
    dashboard.build()

ui.run(title='Sales Dashboard Refactored', port=8081)