from nicegui import ui
import pandas as pd
import plotly.express as px

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
    # ui.row() 相同的样式的KPI卡片，这里用循环简化代码
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

    # # ui.row() 差异化样式的KPI卡片, 直接分开写可能更直观, 便于后续调整, 这里保留
    # with ui.row().classes('w-full gap-4 mb-8 px-10'):
    #     with ui.card().classes('flex-1 p-4 bg-blue-50 border-l-4 border-blue-500'):
    #         ui.label("Total Sales").classes('text-gray-600')
    #         ui.label(f"${total_amount:,.0f}").classes('text-xl font-bold text-blue-700')

    #     with ui.card().classes('flex-1 p-4 bg-green-50 border-l-4 border-green-500'):
    #         ui.label("Total Profit").classes('text-gray-600')
    #         ui.label(f"${total_profit:,.0f}").classes('text-xl font-bold text-green-700')

    #     with ui.card().classes('flex-1 p-4 bg-amber-50 border-l-4 border-amber-500'):
    #         ui.label("Avg Profit Margin").classes('text-gray-600')
    #         margin = (total_profit / total_amount * 100) if total_amount != 0 else 0
    #         ui.label(f"{margin:.1f}%").classes('text-xl font-bold text-amber-700')

    #     with ui.card().classes('flex-1 p-4 bg-purple-50 border-l-4 border-purple-500'):
    #         ui.label("Total Orders").classes('text-gray-600')
    #         ui.label(f"{total_orders:,}").classes('text-xl font-bold text-purple-700')

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
            # 创建 Plotly Figur
            fig2 = px.bar(df_state, x='State', y='Amount', 
                          title='Top 10 States by Sales', template='plotly_white')
            # 调整 layout 让图表更紧凑
            fig2.update_layout(margin=dict(l=20, r=20, t=40, b=20), paper_bgcolor='rgba(0,0,0,0)')
            # 设置颜色区分
            fig2.update_traces(marker_color='#3b82f6') 
            # 渲染图表
            ui.plotly(fig2).classes('w-full h-80')

        # Chart 3: Sales by Customer
        with ui.card().classes('chart-card flex-1'):
            # 创建 Plotly Figur
            fig3 = px.bar(df_customer, x='CustomerName', y='Amount', 
                          title='Top 10 Customers by Sales', template='plotly_white')
            # 调整 layout 让图表更紧凑
            fig3.update_layout(margin=dict(l=20, r=20, t=40, b=20), paper_bgcolor='rgba(0,0,0,0)')
            # 设置颜色区分
            fig3.update_traces(marker_color='#10b981')
            # 渲染图表
            ui.plotly(fig3).classes('w-full h-80')

ui.run(title='Sales Dashboard', port=8081)
