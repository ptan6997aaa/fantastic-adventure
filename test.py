from nicegui import ui
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

# ==========================================
# 1. Data Loading / Mock Data Generation
# ==========================================

# 为了确保代码可直接运行，这里生成模拟数据。
# 如果你有真实的 CSV 文件，请取消注释下方的 read_csv 代码，并注释掉 mock_data 代码。

# --- 真实数据加载 (使用时取消注释) ---
# df_details = pd.read_csv('Details.csv')
# df_orders = pd.read_csv('Orders.csv')
# df_global = pd.merge(df_details, df_orders, on="Order ID", how="inner")

# --- 模拟数据生成 (仅用于演示) ---
def create_mock_data():
    np.random.seed(42)
    n_rows = 500
    categories = ['Furniture', 'Office Supplies', 'Technology']
    sub_categories = ['Chairs', 'Tables', 'Binders', 'Art', 'Phones', 'Copiers']
    states = ['California', 'New York', 'Texas', 'Washington', 'Pennsylvania']
    customers = [f'Customer {i}' for i in range(1, 21)]
    
    data = {
        'Order ID': [f'ORD-{i}' for i in range(n_rows)],
        'Amount': np.random.randint(50, 5000, n_rows),
        'Profit': np.random.randint(-500, 1500, n_rows),
        'Quantity': np.random.randint(1, 10, n_rows),
        'Category': np.random.choice(categories, n_rows),
        'Sub-Category': np.random.choice(sub_categories, n_rows),
        'State': np.random.choice(states, n_rows),
        'CustomerName': np.random.choice(customers, n_rows)
    }
    return pd.DataFrame(data)

df_global = create_mock_data()
# ------------------------------------------

# 2. Data Cleaning
if "Sub-Category" in df_global.columns:
    df_global["Sub-Category"] = df_global["Sub-Category"].astype(str).str.strip()
if "Category" in df_global.columns:
    df_global["Category"] = df_global["Category"].astype(str).str.strip()


@ui.page('/')
def main():
    # --- State Management (状态管理) ---
    # 使用字典存储当前的过滤条件，例如 {'State': 'California'}
    filters = {} 

    # --- CSS Styles ---
    ui.add_head_html('''
        <style>
            .kpi-card { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border-radius: 8px; padding: 16px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
            .kpi-title { font-size: 0.9rem; opacity: 0.9; }
            .kpi-value { font-size: 1.8rem; font-weight: bold; margin-top: 4px; }
            .chart-card { border-radius: 8px; padding: 4px; background: white; box-shadow: 0 2px 4px rgba(0,0,0,0.05); border: 1px solid #eee; }
            .filter-tag { background-color: #e0f2fe; color: #0369a1; padding: 4px 12px; border-radius: 16px; font-size: 0.85rem; display: flex; align-items: center; gap: 8px; }
        </style>
    ''')

    # --- Header & Filter Status ---
    with ui.column().classes('w-full items-center mb-6'):
        ui.label('📊 Interactive Sales Dashboard').classes('text-2xl font-bold text-gray-800')
        ui.label('Click on bars to filter data').classes('text-sm text-gray-500 italic')
        
        # 显示当前激活的过滤器和重置按钮
        filter_container = ui.row().classes('items-center gap-2 min-h-[40px]')
    
    # --- UI Elements Initialization (先占位) ---
    # Row 1: KPIs
    with ui.row().classes('w-full justify-between gap-4 px-10 mb-8'):
        with ui.card().classes('kpi-card flex-1'):
            ui.label('Total Amount').classes('kpi-title')
            kpi_amount = ui.label('$0').classes('kpi-value')
        
        with ui.card().classes('kpi-card flex-1'):
            ui.label('Total Profit').classes('kpi-title')
            kpi_profit = ui.label('$0').classes('kpi-value')
        
        with ui.card().classes('kpi-card flex-1'):
            ui.label('Total Quantity').classes('kpi-title')
            kpi_quantity = ui.label('0').classes('kpi-value')
        
        with ui.card().classes('kpi-card flex-1'):
            ui.label('Order Count').classes('kpi-title')
            kpi_orders = ui.label('0').classes('kpi-value')

    # Row 2: Charts
    with ui.row().classes('w-full justify-between gap-4 px-10'):
        # Chart 1
        with ui.card().classes('chart-card flex-1'):
            chart1 = ui.plotly(go.Figure()).classes('w-full h-80')
        # Chart 2
        with ui.card().classes('chart-card flex-1'):
            chart2 = ui.plotly(go.Figure()).classes('w-full h-80')
        # Chart 3
        with ui.card().classes('chart-card flex-1'):
            chart3 = ui.plotly(go.Figure()).classes('w-full h-80')


    # --- Logic: Refresh Function ---
    def refresh_dashboard():
        """
        根据 filters 字典筛选数据，并更新所有 UI 组件
        """
        # 1. Filter Data
        df_filtered = df_global.copy()
        for col, val in filters.items():
            df_filtered = df_filtered[df_filtered[col] == val]

        # 2. Update Filter UI (显示当前的筛选标签)
        filter_container.clear()
        if filters:
            with filter_container:
                ui.label(f'Filters: ').classes('text-gray-600 font-bold mr-2')
                for k, v in filters.items():
                    ui.label(f'{k}: {v}').classes('filter-tag')
                ui.button('Reset Filters', on_click=reset_filters, icon='close').props('flat dense color=red size=sm')

        # 3. Update KPIs
        total_amount = df_filtered['Amount'].sum()
        total_profit = df_filtered['Profit'].sum()
        total_quantity = df_filtered['Quantity'].sum()
        total_orders = df_filtered['Order ID'].nunique()

        kpi_amount.set_text(f'${total_amount:,.0f}')
        kpi_profit.set_text(f'${total_profit:,.0f}')
        kpi_quantity.set_text(f'{total_quantity:,}')
        kpi_orders.set_text(f'{total_orders:,}')

        # 4. Update Charts
        # Chart 1: Profit by Sub-Category
        df_sub_cat = df_filtered.groupby('Sub-Category')['Profit'].sum().reset_index().sort_values('Profit', ascending=False)
        fig1 = px.bar(df_sub_cat, x='Sub-Category', y='Profit', title='Profit by Sub-Category', template='plotly_white')
        fig1.update_layout(margin=dict(l=20, r=20, t=40, b=20), paper_bgcolor='rgba(0,0,0,0)', clickmode='event+select')
        # 只有在 Sub-Category 没有被筛选时，高亮选中状态才更有意义，但这里我们简单全刷
        chart1.update_figure(fig1)

        # Chart 2: Sales by State
        df_state = df_filtered.groupby('State')['Amount'].sum().reset_index().sort_values('Amount', ascending=False).head(10)
        fig2 = px.bar(df_state, x='State', y='Amount', title='Top States by Sales', template='plotly_white')
        fig2.update_layout(margin=dict(l=20, r=20, t=40, b=20), paper_bgcolor='rgba(0,0,0,0)', clickmode='event+select')
        fig2.update_traces(marker_color='#3b82f6')
        chart2.update_figure(fig2)

        # Chart 3: Sales by Customer
        df_customer = df_filtered.groupby('CustomerName')['Amount'].sum().reset_index().sort_values('Amount', ascending=False).head(10)
        fig3 = px.bar(df_customer, x='CustomerName', y='Amount', title='Top Customers by Sales', template='plotly_white')
        fig3.update_layout(margin=dict(l=20, r=20, t=40, b=20), paper_bgcolor='rgba(0,0,0,0)', clickmode='event+select')
        fig3.update_traces(marker_color='#10b981')
        chart3.update_figure(fig3)

    # --- Interaction Handlers ---

    def handle_click(event, column_name):
        """
        处理图表点击事件
        event.args 包含 Plotly 发回的点击数据。
        对于 bar chart, event.args['points'][0]['x'] 通常是类别名称。
        """
        if 'points' in event.args and len(event.args['points']) > 0:
            click_val = event.args['points'][0]['x']
            
            # 更新 Filter
            filters[column_name] = click_val
            
            # 通知用户
            ui.notify(f'Filtered by {column_name}: {click_val}', type='info')
            
            # 刷新 Dashboard
            refresh_dashboard()

    def reset_filters():
        filters.clear()
        ui.notify('Filters reset', type='positive')
        refresh_dashboard()

    # --- Bind Events ---
    # 为每个图表绑定点击事件，并传入对应的列名
    chart1.on('plotly_click', lambda e: handle_click(e, 'Sub-Category'))
    chart2.on('plotly_click', lambda e: handle_click(e, 'State'))
    chart3.on('plotly_click', lambda e: handle_click(e, 'CustomerName'))

    # --- Initial Load ---
    refresh_dashboard()

ui.run(title='Sales Dashboard', port=8081)