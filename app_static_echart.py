from nicegui import ui
import pandas as pd
from typing import Tuple, Optional

# --- 数据加载与处理（封装为函数，带异常处理）---
def load_and_merge_data(details_path: str = 'Details.csv', orders_path: str = 'Orders.csv') -> pd.DataFrame:
    try:
        df_details = pd.read_csv(details_path)
        df_orders = pd.read_csv(orders_path)
    except FileNotFoundError as e:
        ui.notify(f"数据文件未找到: {e}", type='negative')
        # 可选：生成模拟数据（如你关注的容错机制）
        return pd.DataFrame()
    
    df_global = pd.merge(df_details, df_orders, on="Order ID", how="inner")

    # 清理字符串字段（如存在）
    for col in ["Sub-Category", "Category"]:
        if col in df_global.columns:
            df_global[col] = df_global[col].astype(str).str.strip()
    
    return df_global

# --- 指标与聚合计算 ---
def compute_metrics(df: pd.DataFrame) -> Tuple[float, float, int, int]:
    total_amount = df['Amount'].sum() if 'Amount' in df.columns else 0
    total_profit = df['Profit'].sum() if 'Profit' in df.columns else 0
    total_quantity = df['Quantity'].sum() if 'Quantity' in df.columns else 0
    total_orders = df['Order ID'].nunique() if 'Order ID' in df.columns else 0
    return total_amount, total_profit, total_quantity, total_orders

def compute_aggregates(df: pd.DataFrame):
    df_sub_cat = df.groupby('Sub-Category')['Profit'].sum().reset_index()
    df_sub_cat = df_sub_cat.sort_values(by='Profit', ascending=False)

    df_state = df.groupby('State')['Amount'].sum().reset_index()
    df_state = df_state.sort_values(by='Amount', ascending=False).head(10)

    df_customer = df.groupby('CustomerName')['Amount'].sum().reset_index()
    df_customer = df_customer.sort_values(by='Amount', ascending=False).head(10)

    return df_sub_cat, df_state, df_customer

# --- ECharts 配置生成函数 ---
def create_bar_option(
    title: str, 
    x_data: list, 
    y_data: list, 
    color: Optional[str] = None, 
    rotate_x: bool = False
) -> dict:
    option = {
        'title': {'text': title, 'left': 'center', 'top': '5%'},
        'tooltip': {
            'trigger': 'axis',
            'axisPointer': {'type': 'shadow'}
        },
        'grid': {
            'left': '3%',
            'right': '4%',
            'bottom': '10%' if rotate_x else '3%',
            'containLabel': True
        },
        'xAxis': [{
            'type': 'category',
            'data': x_data,
            'axisTick': {'alignWithLabel': True},
            'axisLabel': {'rotate': 40 if rotate_x else 0}
        }],
        'yAxis': [{'type': 'value'}],
        'series': [{
            'type': 'bar',
            'barWidth': '60%',
            'data': y_data,
        }]
    }
    if color:
        option['series'][0]['itemStyle'] = {'color': color}
    return option

# --- 主页面 ---
@ui.page('/')
def main():
    # 注入 CSS 样式
    ui.add_head_html('''
    <style>
    .kpi-card { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border-radius: 8px; padding: 16px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    .kpi-title { font-size: 0.9rem; opacity: 0.9; }
    .kpi-value { font-size: 1.8rem; font-weight: bold; margin-top: 4px; }
    .chart-card { border-radius: 8px; padding: 4px; background: white; box-shadow: 0 2px 4px rgba(0,0,0,0.05); border: 1px solid #eee; }
    </style>
    ''')

    df_global = load_and_merge_data()
    if df_global.empty:
        ui.label("❌ 无法加载数据，请检查 CSV 文件是否存在。").classes('text-red-500 text-xl')
        return

    total_amount, total_profit, total_quantity, total_orders = compute_metrics(df_global)
    df_sub_cat, df_state, df_customer = compute_aggregates(df_global)

    ui.label('📊 Sales Overview').classes('text-2xl font-bold text-center mb-6 text-gray-800')

    # KPI 卡片
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

    # 图表行
    with ui.row().classes('w-full justify-between gap-4 px-10'):
        # Profit by Sub-Category
        with ui.card().classes('chart-card flex-1'):
            opt1 = create_bar_option(
                title='Profit by Sub-Category',
                x_data=df_sub_cat['Sub-Category'].tolist(),
                y_data=df_sub_cat['Profit'].round(0).tolist(),
                color='#28738a',
                rotate_x=True
            )
            ui.echart(opt1).classes('w-full h-80')

        # Top 10 States
        with ui.card().classes('chart-card flex-1'):
            opt2 = create_bar_option(
                title='Top 10 States by Sales',
                x_data=df_state['State'].tolist(),
                y_data=df_state['Amount'].round(0).tolist(),
                color='#3b82f6',
                rotate_x=True
            )
            ui.echart(opt2).classes('w-full h-80')

        # Top 10 Customers
        with ui.card().classes('chart-card flex-1'):
            opt3 = create_bar_option(
                title='Top 10 Customers by Sales',
                x_data=df_customer['CustomerName'].tolist(),
                y_data=df_customer['Amount'].round(0).tolist(),
                color='#10b981',
                rotate_x=True
            )
            ui.echart(opt3).classes('w-full h-80')

# --- 启动应用 ---
if __name__ in {"__main__", "__mp_main__"}:
    ui.run(title='Sales Dashboard', port=8081)