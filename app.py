from nicegui import ui
import pandas as pd

# --- 1. Data Loading ---
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
filters = {} 

# --- 3. Logic: Filter Data ---
def get_filtered_df(exclude_col=None):
    df_temp = df_global.copy()
    if df_temp.empty: return df_temp
    
    for col, val in filters.items():
        if col == exclude_col:
            continue
        df_temp = df_temp[df_temp[col] == val]
    return df_temp

# --- 4. Logic: Build ECharts Options ---
def build_echart_option(title, x_data, y_data, highlight_val=None, base_color='#3b82f6'):
    series_data = []
    color_selected = base_color
    color_unselected = '#dbeafe' 
    
    for x, y in zip(x_data, y_data):
        is_highlighted = (highlight_val is None) or (x == highlight_val)
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

# --- 5. Main UI Page ---
@ui.page('/')
def main():
    if df_global.empty:
        ui.label("Error: No data found.").classes('text-red-500')
        return

    ui.add_head_html('''
        <style>
            .kpi-card { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border-radius: 8px; padding: 16px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
            .kpi-title { font-size: 0.9rem; opacity: 0.9; }
            .kpi-value { font-size: 1.8rem; font-weight: bold; margin-top: 4px; }
            .chart-card { border-radius: 8px; padding: 4px; background: white; box-shadow: 0 2px 4px rgba(0,0,0,0.05); border: 1px solid #eee; }
            .filter-tag { background-color: #e0f2fe; color: #0369a1; padding: 4px 12px; border-radius: 16px; font-size: 0.85rem; display: flex; align-items: center; gap: 8px; }
        </style>
    ''')

    with ui.column().classes('w-full items-left mb-6'):
        ui.label('📊 Sales Overview (ECharts Final)').classes('text-2xl font-bold text-center mb-6 text-gray-800')
        filter_container = ui.row().classes('items-center gap-2 min-h-[40px] px-10')

    # --- KPIs ---
    kpi_refs = {}
    with ui.row().classes('w-full justify-between gap-4 px-10 mb-8'):
        for key, title in [('amt', 'Total Amount'), ('prf', 'Total Profit'), ('qty', 'Total Quantity'), ('ord', 'Order Count')]:
            with ui.card().classes('kpi-card flex-1'):
                ui.label(title).classes('kpi-title')
                kpi_refs[key] = ui.label('...').classes('kpi-value')

    # --- Charts ---
    with ui.row().classes('w-full justify-between gap-4 px-10'):
        with ui.card().classes('chart-card flex-1'):
            chart1 = ui.echart({'xAxis': {}, 'yAxis': {}, 'series': []}).classes('w-full h-80')
        with ui.card().classes('chart-card flex-1'):
            chart2 = ui.echart({'xAxis': {}, 'yAxis': {}, 'series': []}).classes('w-full h-80')
        with ui.card().classes('chart-card flex-1'):
            chart3 = ui.echart({'xAxis': {}, 'yAxis': {}, 'series': []}).classes('w-full h-80')

    def reset_filters():
        filters.clear()
        ui.notify('Filters reset')
        refresh_dashboard()

    def refresh_dashboard():
        # A. UI
        filter_container.clear()
        if filters:
            with filter_container:
                ui.label('Filters: ').classes('text-gray-600 font-bold')
                for k, v in filters.items():
                    ui.label(f'{k}: {v}').classes('filter-tag')
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
            
            opt = build_echart_option(title, df_grp[group_col].tolist(), df_grp[val_col].round(0).tolist(), filters.get(group_col), color)
            chart.options.clear()
            chart.options.update(opt)
            chart.update()

        update_chart(chart1, get_filtered_df('Sub-Category'), 'Sub-Category', 'Profit', '#28738a', 'Profit by Sub-Category')
        update_chart(chart2, get_filtered_df('State'), 'State', 'Amount', '#3b82f6', 'Top 10 States')
        update_chart(chart3, get_filtered_df('CustomerName'), 'CustomerName', 'Amount', '#10b981', 'Top 10 Customers')

    # --- Event Handler (修正版：使用 on_point_click) ---
    def handle_click(e, col_name):
        # 注意：这里 e 是 EChartPointClickEventArguments 对象
        # 它直接包含 name, value, series_name 等属性，不需要解析 JSON
        
        click_val = e.name 
        print(f"Clicked: {col_name} -> {click_val}") # 调试打印

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
    chart1.on_point_click(lambda e: handle_click(e, 'Sub-Category'))
    chart2.on_point_click(lambda e: handle_click(e, 'State'))
    chart3.on_point_click(lambda e: handle_click(e, 'CustomerName'))

    refresh_dashboard()

ui.run(title='ECharts Final', port=8081)