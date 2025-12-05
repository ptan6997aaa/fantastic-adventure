from nicegui import ui
import pandas as pd

# --- 1. Data Loading --- 
# --- 数据加载与处理 ---
try:
    df_details = pd.read_csv('Details.csv')
    df_orders = pd.read_csv('Orders.csv')
    df_global = pd.merge(df_details, df_orders, on="Order ID", how="inner")

    if "Sub-Category" in df_global.columns:
        df_global["Sub-Category"] = df_global["Sub-Category"].astype(str).str.strip()
    if "Category" in df_global.columns:
        df_global["Category"] = df_global["Category"].astype(str).str.strip()
except Exception as e:
    print(f"Data Error: {e}")
    df_global = pd.DataFrame()

# --- 2. State Management --- 
# --- “筛选状态”管理器 ---
filters = {}  # 全局字典，记录当前筛选条件, 例如：{'State': 'Texas', 'CustomerName': 'Alice'} 

# --- 3. Logic: Filter Data --- 
# --- “筛选数据”函数 --- 
def get_filtered_df(exclude_col=None):
    """
    每次用户点击，都要重新计算 KPI 和图表数据。这个函数能根据 filters 动态返回筛选后的 DataFrame。
    exclude_col 很关键: 比如你点“State”图表时, 不能让 State 自己参与筛选（否则只能看到一个州），所以要排除 
    """
    df_temp = df_global.copy()
    for col, val in filters.items():
        if col == exclude_col: continue  # 图表自身不参与自己的筛选
        df_temp = df_temp[df_temp[col] == val]
    return df_temp

# --- 4. Logic: Build ECharts Options ---
def build_bar_chart_option(title, x_data, y_data, highlight_val=None, base_color='#3b82f6'):
    series_data = []
    color_selected = base_color # 选中颜色，比如蓝色 
    color_unselected = '#dbeafe' # 未选中颜色，浅蓝灰色   
    
    for x, y in zip(x_data, y_data):
        is_highlighted = (highlight_val is None) or (x == highlight_val)
        # 高亮当前选中的柱子 
        # 比如 x_data 是州名，如 'Texas'， 用户点了这个州，那个柱子应该变亮，其他变灰，这样就知道当前筛选状态了 
        # 在 refresh_dashboard() 函数中的 update_chart() 里调用这个函数时，会传入 highlight_val 参数 
        current_color = color_selected if is_highlighted else color_unselected
        series_data.append({'value': y, 'itemStyle': {'color': current_color}})

    option = {
        'title': {'text': title, 'left': 'center', 'top': '5%'},
        'tooltip': {'trigger': 'axis', 'axisPointer': {'type': 'shadow'}},
        'grid': {'left': '3%', 'right': '4%', 'bottom': '10%', 'containLabel': True},
        'xAxis': [{
            'type': 'category',
            'data': x_data,
            'axisTick': {'alignWithLabel': True},
            'axisLabel': {'rotate': 45, 'interval': 0}
        }],
        'yAxis': [{'type': 'value'}],
        'series': [{'type': 'bar', 'barWidth': '60%', 'data': series_data}]
    }
    return option

# KPI, 图表不能在这里只算一次, 比如 
#   1. KPI 的计算 total_amount = df_global['Amount'].sum()
#   2. Bar Chart 的计算 df_sub_cat = df_global.groupby('Sub-Category')['Profit'].sum().reset_index()
# 所有计算都移到 refresh_dashboard() 函数里，每次筛选后重新算 

# --- Dashboard ---
@ui.page('/')
def main():
    ui.add_head_html('''
        <style>
            .kpi-card { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border-radius: 8px; padding: 16px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
            .kpi-title { font-size: 0.9rem; opacity: 0.9; }
            .kpi-value { font-size: 1.8rem; font-weight: bold; margin-top: 4px; }
            .chart-card { border-radius: 8px; padding: 4px; background: white; box-shadow: 0 2px 4px rgba(0,0,0,0.05); border: 1px solid #eee; } 
            .filter-tag { background-color: #e0f2fe; color: #0369a1; padding: 4px 12px; border-radius: 16px; font-size: 0.85rem; display: flex; align-items: center; gap: 8px; } 
        </style>
    ''')

    ui.label('📊 Sales Overview').classes('text-2xl font-bold text-center mb-6 text-gray-800') 
    # 创建一个可重复更新的 UI 区域 
    filter_container = ui.row().classes('items-center gap-2 min-h-[40px] px-10')

    # --- KPIs --- 
    # 用 kpi_refs = {} 保存 KPI 标签的引用，这样后面才能用 .set_text() 修改它 
    kpi_refs = {}
    # KPI 占位符，稍后刷新时更新  
    with ui.row().classes('w-full justify-between gap-4 px-10 mb-8'):
        for key, title in [('amt', 'Total Amount'), ('prf', 'Total Profit'), ('qty', 'Total Quantity'), ('ord', 'Order Count')]:
            with ui.card().classes('kpi-card flex-1'):
                ui.label(title).classes('kpi-title')
                kpi_refs[key] = ui.label('...').classes('kpi-value')

    # --- Charts --- 
    # 图表占位符，稍后刷新时更新  
    with ui.row().classes('w-full justify-between gap-4 px-10'):
        with ui.card().classes('chart-card flex-1'):
            # 图表初始为空，refresh_dashboard() 里调用 update_chart() 重新生成 option 并更新 
            chart1 = ui.echart({'xAxis': {}, 'yAxis': {}, 'series': []}).classes('w-full h-80')
        with ui.card().classes('chart-card flex-1'):
            # 图表初始为空，refresh_dashboard() 里调用 update_chart() 重新生成 option 并更新 
            chart2 = ui.echart({'xAxis': {}, 'yAxis': {}, 'series': []}).classes('w-full h-80')
        with ui.card().classes('chart-card flex-1'):
            # 图表初始为空，refresh_dashboard() 里调用 update_chart() 重新生成 option 并更新  
            chart3 = ui.echart({'xAxis': {}, 'yAxis': {}, 'series': []}).classes('w-full h-80')

    def reset_filters():
        filters.clear()
        ui.notify('Filters reset')
        refresh_dashboard()
    
    def refresh_dashboard():
        # A. UI - 清空并重新渲染筛选标签区域 
        # 每次刷新前清除旧标签，避免重复叠加  
        filter_container.clear() # 先清空之前的内容, 比如 "State: Texas"  
        if filters: # 只有筛选存在时才显示，干净简洁 
            # 显示当前筛选条件 + 清除按钮 
            with filter_container: # 把新内容“写入”这个容器 
                ui.label('Filters: ').classes('text-gray-600 font-bold')
                for k, v in filters.items():
                    ui.label(f'{k}: {v}').classes('filter-tag') # 比如 "State: Texas" 
                ui.button(icon='close', on_click=reset_filters).props('flat round dense color=red')

        # B. KPI
        df_kpi = get_filtered_df(exclude_col=None)
        kpi_refs['amt'].set_text(f"${df_kpi['Amount'].sum():,.0f}")
        kpi_refs['prf'].set_text(f"${df_kpi['Profit'].sum():,.0f}")
        kpi_refs['qty'].set_text(f"{df_kpi['Quantity'].sum():,}")
        kpi_refs['ord'].set_text(f"{df_kpi['Order ID'].nunique():,}")

        # C. Charts
        def update_chart(chart, df, group_col, val_col, color, title):
            df_grp = df.groupby(group_col)[val_col].sum().reset_index().sort_values(val_col, ascending=False)
            if group_col != 'Sub-Category': df_grp = df_grp.head(10)
            
            # filters.get('categorical data 比如（州、客户、子类）') 不是直接写在 build_bar_chart_option 调用处的字面量，而是通过 group_col 动态决定的，这让代码能复用于不同图表（州、客户、子类） 
            opt = build_bar_chart_option(title, df_grp[group_col].tolist(), df_grp[val_col].round(0).tolist(), filters.get(group_col), color)
            chart.options.clear()
            chart.options.update(opt)
            chart.update()

        update_chart(chart1, get_filtered_df('Sub-Category'), 'Sub-Category', 'Profit', '#28738a', 'Profit by Sub-Category')
        update_chart(chart2, get_filtered_df('State'), 'State', 'Amount', '#3b82f6', 'Top 10 States')
        update_chart(chart3, get_filtered_df('CustomerName'), 'CustomerName', 'Amount', '#10b981', 'Top 10 Customers')
    
    # --- Event Handler --- 
    def handle_click(e, col_name):
        """
        如果点的是已选中的项 → 取消筛选（从 filters 删除）
        如果是新项 → 加入 filters
        然后调用 refresh_dashboard() 重新渲染一切 
        """
        # 注意：这里 e 是 EChartPointClickEventArguments 对象
        # 它直接包含 name, value, series_name 等属性，不需要解析 JSON
        
        click_val = e.name  # e.name 就是柱子的类别名（如 "Texas"） 
        # # 调试打印
        # print(f"Clicked: {col_name} -> {click_val}") 

        if not click_val: return

        if filters.get(col_name) == click_val:
            filters.pop(col_name)
            ui.notify(f'Removed filter: {col_name}')
        else:
            filters[col_name] = click_val
            ui.notify(f'Filtered by {col_name}: {click_val}') 
        
        refresh_dashboard()

    # --- 关键修改：使用 on_point_click ---
    # 这是 NiceGUI 专门处理 ECharts 点击的方法，比 .on('click') 更稳定 
    # NiceGUI 的 ECharts 组件提供了 on_point_click 事件，它会传入一个对象 e，其中 e.name 就是柱子的类别名（如 "Texas"） 
    chart1.on_point_click(lambda e: handle_click(e, 'Sub-Category'))
    chart2.on_point_click(lambda e: handle_click(e, 'State'))
    chart3.on_point_click(lambda e: handle_click(e, 'CustomerName'))

    refresh_dashboard() 

ui.run(title='Sales Dashboard', port=8081) 