from nicegui import ui
import pandas as pd
import plotly.express as px

# 1. Load Data
try:
    df_details = pd.read_csv('Details.csv')
    df_orders = pd.read_csv('Orders.csv')
except FileNotFoundError:
    # 为了演示代码运行，如果没有文件，这里生成一些假数据
    # 实际运行时请删除这块 try-except，保留你的 pd.read_csv
    print("未找到CSV文件，使用模拟数据...")
    data = {
        'Order ID': [f'ORD-{i}' for i in range(100)],
        'Amount': [i * 10 for i in range(100)],
        'Profit': [i * 2 for i in range(100)],
        'Quantity': [i % 5 + 1 for i in range(100)],
        'Category': ['Office'] * 50 + ['Tech'] * 50,
        'Sub-Category': ['Phones', 'Binders', 'Chairs', 'Storage'] * 25,
        'State': ['CA', 'NY', 'TX', 'WA', 'FL'] * 20,
        'CustomerName': [f'Customer {i}' for i in range(100)]
    }
    df_details = pd.DataFrame(data)
    df_orders = pd.DataFrame(data)
    # 模拟数据结束

# 2. Merge Data
df_global = pd.merge(df_details, df_orders, on="Order ID", how="inner")

# 3. Data Cleaning
# 处理列名可能存在的重复（merge有时会产生 _x, _y），这里假设没有冲突
# 清理字符串空白
if "Sub-Category" in df_global.columns:
    df_global["Sub-Category"] = df_global["Sub-Category"].astype(str).str.strip()
if "Category" in df_global.columns:
    df_global["Category"] = df_global["Category"].astype(str).str.strip()

# 4. Calculate Global KPIs
total_amount = df_global['Amount'].sum()
total_profit = df_global['Profit'].sum()
total_quantity = df_global['Quantity'].sum()
total_orders = df_global['Order ID'].nunique()

# ==========================================
# 5. Prepare Chart Data (Aggregation)
# ==========================================

# Chart 1: Total Profit by Sub-Category (Sorted)
df_sub_cat = df_global.groupby('Sub-Category')['Profit'].sum().reset_index()
df_sub_cat = df_sub_cat.sort_values(by='Profit', ascending=False)

# Chart 2: Total Sales by State (Top 10)
df_state = df_global.groupby('State')['Amount'].sum().reset_index()
df_state = df_state.sort_values(by='Amount', ascending=False).head(10) # 只取前10，防止图表太挤

# Chart 3: Total Sales by Customer (Top 10)
df_customer = df_global.groupby('CustomerName')['Amount'].sum().reset_index()
df_customer = df_customer.sort_values(by='Amount', ascending=False).head(10) # 只取前10


# ==========================================
# 6. Dashboard Layout
# ==========================================
@ui.page('/')
def main():
    # --- CSS Styles ---
    ui.add_head_html('''
        <style>
            .kpi-card { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border-radius: 8px; padding: 16px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
            .kpi-title { font-size: 0.9rem; opacity: 0.9; }
            .kpi-value { font-size: 1.8rem; font-weight: bold; margin-top: 4px; }
            .chart-card { border-radius: 8px; padding: 4px; background: white; box-shadow: 0 2px 4px rgba(0,0,0,0.05); border: 1px solid #eee; }
        </style>
    ''')

    # --- Header ---
    ui.label('📊 Sales Overview').classes('text-2xl font-bold text-center mb-6 text-gray-800')

    # --- ROW 1: KPIs ---
    # 相同的样式的KPI卡片，这里用循环简化代码
    with ui.row().classes('w-full justify-between gap-4 px-10 mb-8'):
        for title, value in [
            ('Total Amount', f'${total_amount:,.0f}'),
            ('Total Profit', f'${total_profit:,.0f}'),
            ('Total Quantity', f'{total_quantity:,}'),
            ('Order Count', f'{total_orders:,}'),
        ]:
            with ui.card().classes('kpi-card flex-1'):
                ui.label(title).classes('kpi-title')
                ui.label(value).classes('kpi-value')
    
    # 差异化样式的KPI卡片, 直接分开写可能更直观, 便于后续调整, 这里保留 
    with ui.grid(columns=4).classes('w-full gap-4 mb-6'):
        with ui.card().classes('p-4 bg-blue-50 border-l-4 border-blue-500'):
            ui.label("Total Sales").classes('text-gray-600')
            self.kpi_sales = ui.label("$0").classes('text-xl font-bold text-blue-700')
        with ui.card().classes('p-4 bg-green-50 border-l-4 border-green-500'):
            ui.label("Total Profit").classes('text-gray-600')
            self.kpi_profit = ui.label("$0").classes('text-xl font-bold text-green-700')
        with ui.card().classes('p-4 bg-amber-50 border-l-4 border-amber-500'):
            ui.label("Avg Profit Margin").classes('text-gray-600')
            self.kpi_margin = ui.label("0%").classes('text-xl font-bold text-amber-700')
        with ui.card().classes('p-4 bg-purple-50 border-l-4 border-purple-500'):
            ui.label("Total Orders").classes('text-gray-600')
            self.kpi_orders = ui.label("0").classes('text-xl font-bold text-purple-700')

    # --- ROW 2: Bar Charts ---
    # 使用 flex-1 让三个图表平分宽度
    with ui.row().classes('w-full justify-between gap-4 px-10'):
        
        # Chart 1: Profit by Sub-Category
        with ui.card().classes('chart-card flex-1'):
            # 创建 Plotly Figure
            fig1 = px.bar(df_sub_cat, x='Sub-Category', y='Profit', 
                          title='Profit by Sub-Category', template='plotly_white')
            # 调整 layout 让图表更紧凑
            fig1.update_layout(margin=dict(l=20, r=20, t=40, b=20), paper_bgcolor='rgba(0,0,0,0)')
            # 渲染图表
            ui.plotly(fig1).classes('w-full h-80')

        # Chart 2: Sales by State
        with ui.card().classes('chart-card flex-1'):
            fig2 = px.bar(df_state, x='State', y='Amount', 
                          title='Top 10 States by Sales', template='plotly_white')
            fig2.update_layout(margin=dict(l=20, r=20, t=40, b=20), paper_bgcolor='rgba(0,0,0,0)')
            # 设置颜色区分
            fig2.update_traces(marker_color='#3b82f6') 
            ui.plotly(fig2).classes('w-full h-80')

        # Chart 3: Sales by Customer
        with ui.card().classes('chart-card flex-1'):
            fig3 = px.bar(df_customer, x='CustomerName', y='Amount', 
                          title='Top 10 Customers by Sales', template='plotly_white')
            fig3.update_layout(margin=dict(l=20, r=20, t=40, b=20), paper_bgcolor='rgba(0,0,0,0)')
            # 设置颜色区分
            fig3.update_traces(marker_color='#10b981')
            ui.plotly(fig3).classes('w-full h-80')

ui.run(title='Sales Dashboard', port=8081)