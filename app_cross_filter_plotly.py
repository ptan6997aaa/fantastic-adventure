from nicegui import ui
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 1. Load Data
# Details.csv 包含：订单明细（金额、利润、品类、子品类、支付方式等）
# Orders.csv 包含：订单主信息（订单日期、客户、城市、州等）
# 这两行会把两个文件读入内存，生成两个 DataFrame 对象 
# 脚本与 Details.csv、Orders.csv 在同一目录下，否则要写完整路径 
df_details = pd.read_csv('Details.csv')
df_orders = pd.read_csv('Orders.csv')

# 2. Merge Data
# 使用 pd.merge() 将两个表按 "Order ID" 字段内连接（inner join）。
# 结果 df_global 会包含：
# 所有 Details.csv 的字段（Amount, Profit, Category...）
# 所有 Orders.csv 的字段（Order Date, CustomerName, State, City...）
# 只保留两个表中都存在的 Order ID (inner join 的特性)  
df_global = pd.merge(df_details, df_orders, on="Order ID", how="inner")

# 3. Data Cleaning
# 防止因 " Electronics " 和 "Electronics" 被识别为不同类别。
# .astype(str) 确保即使有空值（NaN）也不会报错（NaN 会变成 "nan" 字符串，但通常数据中不应有）。
# .str.strip() 去除字符串首尾空格
if "Sub-Category" in df_global.columns:
    df_global["Sub-Category"] = df_global["Sub-Category"].astype(str).str.strip()
if "Category" in df_global.columns:
    df_global["Category"] = df_global["Category"].astype(str).str.strip()

# 4. Calculate Global KPIs
# Total Amount 
total_amount = df_global['Amount'].sum()
# Total Profit
total_profit = df_global['Profit'].sum()
# Total Quantity
total_quantity = df_global['Quantity'].sum()
# Total Counts of Orders 
total_orders = df_global['Order ID'].nunique() 

# 5. Prepare Chart Data 
# Chart 1: Total Profit by Sub-Category (Sorted)
df_sub_cat = df_global.groupby('Sub-Category')['Profit'].sum().reset_index()
df_sub_cat = df_sub_cat.sort_values(by='Profit', ascending=False)

# Chart 2: Total Sales by State (Top 10)
df_state = df_global.groupby('State')['Amount'].sum().reset_index()
df_state = df_state.sort_values(by='Amount', ascending=False).head(10) # 只取前10，防止图表太挤

# Chart 3: Total Sales by Customer (Top 10)
df_customer = df_global.groupby('CustomerName')['Amount'].sum().reset_index()
df_customer = df_customer.sort_values(by='Amount', ascending=False).head(10) # 只取前10

# 6. Dashboard Layout
@ui.page('/')
def main():
    # Cross Filter Logic  
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

    # --- Header ---
    with ui.column().classes('w-full items-left mb-6'):
        # 显示标题 
        ui.label('📊 Sales Overview').classes('text-2xl font-bold text-center mb-6 text-gray-800') 
        # 显示当前激活的过滤器和重置按钮
        filter_container = ui.row().classes('items-center gap-2 min-h-[40px]')

    # Cross Filter Logic 
    # 先占位, 后续通过 .set_text() 或 .update_figure() 动态更新 
    # KPI 占位示例：kpi_amount = ui.label('$0').classes('kpi-value') 
    # 图表占位示例：chart1 = ui.plotly(go.Figure()).classes('w-full h-80')  
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

    # Cross Filter Logic 
    # 编写 get_filtered_df(exclude_col=None) 函数, 这是 cross-filter 的关键逻辑 
    #     1. 当渲染“子品类”图表时，忽略子品类的筛选条件，这样即使用户点了“Chairs”，图表仍显示所有子品类（但高亮 Chairs）
    #     2. 但 KPI 要应用所有筛选
    def get_filtered_df(exclude_col=None):
        """
        获取过滤后的数据。
        exclude_col: 为了实现交叉筛选，渲染某个图表时，应该排除它自己的过滤条件，
        这样它才能显示全局上下文，并高亮选中项。
        """
        df_temp = df_global.copy()
        for col, val in filters.items():
            # 如果是当前图表对应的列，跳过过滤（保留该列所有数据以便展示）
            if col == exclude_col:
                continue
            df_temp = df_temp[df_temp[col] == val]
        return df_temp

    # Cross Filter Logic 
    # 编写 refresh_dashboard() 函数 
    # 这个函数负责：
    #   1. 顶部筛选标签（显示当前筛选 + 重置按钮）
    #   2. 重新计算 KPI（用 get_filtered_df(None)）
    #   3. 重新生成三个图表（分别调用 get_filtered_df('Sub-Category') 等）
    #   4. 为图表柱子设置颜色：选中项深色，其他浅色
    #   5. 在 fig.update_layout(...) 中加入 clickmode='event+select' 启用 Plotly 的点击模式, 否则事件不会触发 
    def refresh_dashboard():
        """
        根据 filters 字典筛选数据，并更新所有 UI 组件
        """
          
        # 1. Filter UI 
        # 增加重置筛选功能, 仅当有筛选时出现重置按钮  
        filter_container.clear()
        if filters:
            with filter_container:
                ui.label(f'Filters: ').classes('text-gray-600 font-bold mr-2')
                for k, v in filters.items():
                    ui.label(f'{k}: {v}').classes('filter-tag')
                ui.button('Reset Filters', on_click=reset_filters, icon='close').props('flat dense color=red size=sm')

        # 2. Update KPIs (KPI 必须反映所有过滤器的结果)
        df_kpi = get_filtered_df(exclude_col=None) # 不排除任何条件
        total_amount = df_kpi['Amount'].sum()
        total_profit = df_kpi['Profit'].sum()
        total_quantity = df_kpi['Quantity'].sum()
        total_orders = df_kpi['Order ID'].nunique()

        kpi_amount.set_text(f'${total_amount:,.0f}')
        kpi_profit.set_text(f'${total_profit:,.0f}')
        kpi_quantity.set_text(f'{total_quantity:,}')
        kpi_orders.set_text(f'{total_orders:,}')

        # 3. Update Charts (使用 Cross-Filtering 逻辑)
        
        # --- Chart 1: Profit by Sub-Category ---
        # 排除 Sub-Category 自己的筛选，这样即使用户点了 Chairs，柱状图依然显示所有子类
        df_c1 = get_filtered_df(exclude_col='Sub-Category')
        df_sub_cat = df_c1.groupby('Sub-Category')['Profit'].sum().reset_index().sort_values('Profit', ascending=False)
        
        # 计算颜色: 如果有筛选，选中的显示深色，未选中的显示浅色
        selected_sub = filters.get('Sub-Category')
        # 如果没有筛选，默认全深色；如果有筛选，选中的深色，其他的浅色
        colors_c1 = ['#3b82f6' if (not selected_sub or x == selected_sub) else '#dbeafe' for x in df_sub_cat['Sub-Category']]
        
        fig1 = px.bar(df_sub_cat, x='Sub-Category', y='Profit', title='Profit by Sub-Category', template='plotly_white')
        fig1.update_layout(margin=dict(l=20, r=20, t=40, b=20), paper_bgcolor='rgba(0,0,0,0)', clickmode='event+select')
        fig1.update_traces(marker_color=colors_c1) # 应用颜色
        chart1.update_figure(fig1)

        # --- Chart 2: Sales by State ---
        df_c2 = get_filtered_df(exclude_col='State')
        df_state = df_c2.groupby('State')['Amount'].sum().reset_index().sort_values('Amount', ascending=False).head(10)
        
        selected_state = filters.get('State')
        colors_c2 = ['#3b82f6' if (not selected_state or x == selected_state) else '#dbeafe' for x in df_state['State']]

        fig2 = px.bar(df_state, x='State', y='Amount', title='Top States by Sales', template='plotly_white')
        fig2.update_layout(margin=dict(l=20, r=20, t=40, b=20), paper_bgcolor='rgba(0,0,0,0)', clickmode='event+select')
        fig2.update_traces(marker_color=colors_c2)
        chart2.update_figure(fig2)

        # --- Chart 3: Sales by Customer ---
        df_c3 = get_filtered_df(exclude_col='CustomerName')
        df_customer = df_c3.groupby('CustomerName')['Amount'].sum().reset_index().sort_values('Amount', ascending=False).head(10)
        
        selected_cust = filters.get('CustomerName')
        colors_c3 = ['#10b981' if (not selected_cust or x == selected_cust) else '#d1fae5' for x in df_customer['CustomerName']]

        fig3 = px.bar(df_customer, x='CustomerName', y='Amount', title='Top Customers by Sales', template='plotly_white')
        fig3.update_layout(margin=dict(l=20, r=20, t=40, b=20), paper_bgcolor='rgba(0,0,0,0)', clickmode='event+select')
        fig3.update_traces(marker_color=colors_c3)
        chart3.update_figure(fig3)

    # Cross Filter Logic 
    # 清除所有当前激活的筛选条件，恢复仪表板到初始的“无筛选”状态 
    def reset_filters():
            filters.clear()
            ui.notify('Filters reset', type='positive')
            refresh_dashboard()
    
    # Cross Filter Logic 
    # 监听图表点击事件 
    # 使用 chart.on('plotly_click', ...) 捕获点击  
    def handle_click(event, column_name):
        """
        处理图表点击事件
        """
        if 'points' in event.args and len(event.args['points']) > 0:
            # 注意：event.args['points'][0]['x'] 依赖于你的 X 轴是类别名（如 State 名）。如果 X 是数值，需调整 
            click_val = event.args['points'][0]['x']
            
            # # 这里简单处理：直接更新 
            # filters[column_name] = click_val
            
            # ui.notify(f'Filtered by {column_name}: {click_val}', type='info')
            # refresh_dashboard()

            # 优化: 如果点击的是当前已经选中的值, 说明用户想取消这个筛选 
            if filters.get(column_name) == click_val:
                filters.pop(column_name) # 移除筛选
                ui.notify(f'Removed filter: {column_name}', type='info')
            else:
                # 否则，应用新的筛选
                filters[column_name] = click_val
                ui.notify(f'Filtered by {column_name}: {click_val}', type='info')
            
            refresh_dashboard()

    chart1.on('plotly_click', lambda e: handle_click(e, 'Sub-Category'))
    chart2.on('plotly_click', lambda e: handle_click(e, 'State'))
    chart3.on('plotly_click', lambda e: handle_click(e, 'CustomerName'))

    # Cross Filter Logic 
    # 初始加载调用 refresh_dashboard() 
    refresh_dashboard() 

ui.run(title='Sales Dashboard', port=8081)