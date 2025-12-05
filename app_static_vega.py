from nicegui import ui
import pandas as pd
import altair as alt
import json

# 1. Load Data
df_details = pd.read_csv('Details.csv')
df_orders = pd.read_csv('Orders.csv')

# 2. Merge Data
df_global = pd.merge(df_details, df_orders, on="Order ID", how="inner")

# 3. Data Cleaning
if "Sub-Category" in df_global.columns:
    df_global["Sub-Category"] = df_global["Sub-Category"].astype(str).str.strip()
if "Category" in df_global.columns:
    df_global["Category"] = df_global["Category"].astype(str).str.strip()
if "State" in df_global.columns:
    df_global["State"] = df_global["State"].astype(str).str.strip()
if "CustomerName" in df_global.columns:
    df_global["CustomerName"] = df_global["CustomerName"].astype(str).str.strip()

# 4. Global KPIs
total_amount = df_global['Amount'].sum()
total_profit = df_global['Profit'].sum()
total_quantity = df_global['Quantity'].sum()
total_orders = df_global['Order ID'].nunique()

# 5. Prepare Chart DataFrames
df_sub_cat = (
    df_global.groupby('Sub-Category')['Profit']
    .sum()
    .reset_index()
    .sort_values(by='Profit', ascending=False)
)

df_state = (
    df_global.groupby('State')['Amount']
    .sum()
    .reset_index()
    .sort_values(by='Amount', ascending=False)
    .head(10)
)

df_customer = (
    df_global.groupby('CustomerName')['Amount']
    .sum()
    .reset_index()
    .sort_values(by='Amount', ascending=False)
    .head(10)
)

# 6. Generate Altair Charts → Vega-Lite specs
def make_bar_chart(data, x_col, y_col, title, x_title, y_title, color='#4c78a8'):
    chart = (
        alt.Chart(data)
        .mark_bar(color=color)
        .encode(
            x=alt.X(f'{x_col}:N', sort='-y', axis=alt.Axis(labelAngle=-45, title=x_title)),
            y=alt.Y(f'{y_col}:Q', title=y_title),
            tooltip=[
                alt.Tooltip(x_col, title=x_title),
                alt.Tooltip(y_col, title=y_title, format=',.0f'),
            ],
        )
        .properties(
            title=title,
            width='container',
            height=300,
        )
    )
    return chart.to_dict()

spec_subcat = make_bar_chart(df_sub_cat, 'Sub-Category', 'Profit', 'Profit by Sub-Category', 'Sub-Category', 'Profit', '#6366f1')
spec_state  = make_bar_chart(df_state, 'State', 'Amount', 'Top 10 States by Sales', 'State', 'Sales', '#3b82f6')
spec_customer = make_bar_chart(df_customer, 'CustomerName', 'Amount', 'Top 10 Customers by Sales', 'Customer Name', 'Sales', '#10b981')

# Convert to JSON strings for embedding in HTML
spec_subcat_json = json.dumps(spec_subcat)
spec_state_json = json.dumps(spec_state)
spec_customer_json = json.dumps(spec_customer)

@ui.page('/')
def main():
    ui.add_head_html(f'''
        <script src="https://cdn.jsdelivr.net/npm/vega@5"></script>
        <script src="https://cdn.jsdelivr.net/npm/vega-lite@5"></script>
        <script src="https://cdn.jsdelivr.net/npm/vega-embed@6"></script>
        <script>
            const SPEC_SUBCAT = {spec_subcat_json};
            const SPEC_STATE = {spec_state_json};
            const SPEC_CUSTOMER = {spec_customer_json};

            function embedChart(id, spec) {{
                const el = document.getElementById(id);
                if (el) {{
                    vegaEmbed(el, spec, {{actions: false}});
                }}
            }}

            document.addEventListener('DOMContentLoaded', () => {{
                embedChart('chart-subcat', SPEC_SUBCAT);
                embedChart('chart-state', SPEC_STATE);
                embedChart('chart-customer', SPEC_CUSTOMER);
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
            .chart-card {{
                border-radius: 8px;
                padding: 4px;
                background: white;
                box-shadow: 0 2px 4px rgba(0,0,0,0.05);
                border: 1px solid #eee;
            }}
        </style>
    ''')

    ui.label('📊 Sales Overview').classes('text-2xl font-bold text-center mb-6 text-gray-800')

    # --- ROW 1: KPIs ---
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

    # --- ROW 2: Charts (All Vega-Lite) ---
    with ui.row().classes('w-full justify-between gap-4 px-10'):
        with ui.card().classes('chart-card flex-1'):
            ui.html('<div id="chart-subcat" style="width:100%; height:100%;"></div>', sanitize=False).classes('w-full h-80')

        with ui.card().classes('chart-card flex-1'):
            ui.html('<div id="chart-state" style="width:100%; height:100%;"></div>', sanitize=False).classes('w-full h-80')

        with ui.card().classes('chart-card flex-1'):
            ui.html('<div id="chart-customer" style="width:100%; height:100%;"></div>', sanitize=False).classes('w-full h-80')

ui.run(title='Sales Dashboard (Vega-Lite Only)', port=8081)