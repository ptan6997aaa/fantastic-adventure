from nicegui import ui
import pandas as pd
import altair as alt
import json


# ======================
# 1. Load and clean data
# ======================
df_details = pd.read_csv('Details.csv')
df_orders = pd.read_csv('Orders.csv')
df = pd.merge(df_details, df_orders, on="Order ID", how="inner")

df.rename(columns={'Sub Category': 'Sub-Category', 'Customer Name': 'CustomerName'}, inplace=True)
for col in ['Sub-Category', 'Category', 'State', 'CustomerName']:
    if col in df.columns:
        df[col] = df[col].astype(str).str.strip()
        
total_amount = df['Amount'].sum()
total_profit = df['Profit'].sum()
total_quantity = df['Quantity'].sum()
total_orders = df['Order ID'].nunique()

# ======================
# 2. Build Altair Cross-Filter Charts
# ======================


# Define selections
subcat_selection = alt.selection_point(fields=['Sub-Category'], name='subcat')
state_selection = alt.selection_point(fields=['State'], name='state')
customer_selection = alt.selection_point(fields=['CustomerName'], name='customer')


# Chart 1: Profit by Sub-Category (filtered by customer)
chart1 = alt.Chart(df).transform_filter(
    customer_selection  # 新增：响应 customer 筛选
).mark_bar().encode(
    x=alt.X('Sub-Category:N', sort='-y', axis=alt.Axis(labelAngle=-45)),
    y=alt.Y('sum(Profit):Q', title='Profit'),
    color=alt.condition(subcat_selection, alt.value('#ef4444'), alt.value('#3b82f6')),
    tooltip=['Sub-Category:N', 'sum(Profit):Q']
).properties(
    title='Profit by Sub-Category',
    width=300,
    height=300
).add_params(
    subcat_selection
)


# Chart 2: Top 10 States by Sales (filtered by subcat AND customer)
chart2 = alt.Chart(df).transform_filter(
    subcat_selection
).transform_filter(
    customer_selection  # 新增
).transform_aggregate(
    Amount='sum(Amount)',
    groupby=['State']
).transform_window(
    rank='row_number()',
    sort=[alt.SortField('Amount', order='descending')]
).transform_filter(
    alt.datum.rank <= 10
).mark_bar().encode(
    x=alt.X('State:N', sort='-y', axis=alt.Axis(labelAngle=-45)),
    y=alt.Y('Amount:Q', title='Sales (Amount)'),
    color=alt.condition(state_selection, alt.value('#ef4444'), alt.value('#3b82f6')),
    tooltip=['State:N', 'Amount:Q']
).properties(
    title='Top 10 States by Sales',
    width=300,
    height=300
).add_params(
    state_selection
)


# Chart 3: Top 10 Customers by Sales (filtered by subcat & state, and now selectable)
chart3 = alt.Chart(df).transform_filter(
    subcat_selection
).transform_filter(
    state_selection
).transform_aggregate(
    Amount='sum(Amount)',
    groupby=['CustomerName']
).transform_window(
    rank='row_number()',
    sort=[alt.SortField('Amount', order='descending')]
).transform_filter(
    alt.datum.rank <= 10
).mark_bar().encode(
    x=alt.X('CustomerName:N', sort='-y', axis=alt.Axis(labelAngle=-45)),
    y=alt.Y('Amount:Q', title='Sales (Amount)'),
    color=alt.condition(customer_selection, alt.value('#f59e0b'), alt.value('#10b981')),  # 高亮选中项
    tooltip=['CustomerName:N', 'Amount:Q']
).properties(
    title='Top 10 Customers by Sales',
    width=300,
    height=300
).add_params(
    customer_selection  # 新增：使 Chart 3 可点击
)


# Combine charts horizontally
combined = alt.hconcat(
    chart1, chart2, chart3,
    spacing=20
).configure(
    background='white',
    view=alt.ViewConfig(stroke=None)  # remove gray border around each chart
)


# Convert to JSON spec for embedding
spec_json = combined.to_json(indent=None)



# ======================
# 3. NiceGUI Page
# ======================
@ui.page('/')
def main():
    ui.add_head_html(f'''
        <script src="https://cdn.jsdelivr.net/npm/vega@5    "></script>
        <script src="https://cdn.jsdelivr.net/npm/vega-lite@5    "></script>
        <script src="https://cdn.jsdelivr.net/npm/vega-embed@6    "></script>
        <script>
            document.addEventListener('DOMContentLoaded', () => {{
                const spec = {spec_json};
                vegaEmbed('#viz-container', spec, {{ actions: false }})
                    .catch(console.error);
            }});
        </script>
        <style>
            .kpi-card {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border-radius: 8px;
                padding: 16px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }}
            .kpi-title {{ font-size: 0.9rem; opacity: 0.9; }}
            .kpi-value {{ font-size: 1.8rem; font-weight: bold; margin-top: 4px; }}
            .viz-wrapper {{
                background: white;
                border-radius: 8px;
                padding: 20px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.05);
                border: 1px solid #eee;
                overflow-x: auto;
                display: flex;
                justify-content: center;
            }}
        </style>
    ''')


    ui.label('📊 Sales Dashboard - Cross-Filter (Altair)').classes('text-2xl font-bold text-center mb-6')


    # KPI Row
    with ui.row().classes('w-full justify-between gap-4 px-10 mb-6'):
        for title, value in [
            ('Total Amount', f'${total_amount:,.0f}'),
            ('Total Profit', f'${total_profit:,.0f}'),
            ('Total Quantity', f'{total_quantity:,}'),
            ('Order Count', f'{total_orders:,}'),
        ]:
            with ui.card().classes('kpi-card flex-1'):
                ui.label(title).classes('kpi-title')
                ui.label(value).classes('kpi-value')


    # Chart container
    with ui.row().classes('w-full px-10'):
        with ui.element('div').classes('viz-wrapper w-full'):
            ui.html('<div id="viz-container"></div>', sanitize=False)


    ui.label('💡 联动说明：点击 Chart 1 → 过滤 Chart 2 & 3；点击 Chart 2 → 过滤 Chart 3').classes('text-center mt-4 text-lg text-blue-600')



# ======================
# 4. Run App
# ======================
ui.run(title='Cross-Filter Dashboard (Altair)', port=8081) 