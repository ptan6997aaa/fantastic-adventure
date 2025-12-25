from nicegui import ui
import pandas as pd
import plotly.express as px

# ==========================================
# 1. DATA LAYER
# Responsibilities: Loading, Merging, Cleaning
# ==========================================
def get_sales_data():
    """
    Reads CSV files, performs inner join, and cleans string columns.
    Returns: A tuple of (df_global, df_for_kpis) or just the main dataframe.
    """
    try:
        # Load Data
        df_details = pd.read_csv('Details.csv')
        df_orders = pd.read_csv('Orders.csv')
        
        # Merge Data (Inner Join)
        df = pd.merge(df_details, df_orders, on="Order ID", how="inner")
        
        # Cleaning: Handle potential string issues in categories
        for col in ['Sub-Category', 'Category']:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip()
                
        return df
    except FileNotFoundError:
        ui.notify("Error: CSV files not found. Please ensure Details.csv and Orders.csv exist.", type='negative')
        return pd.DataFrame() # Return empty DF to prevent crash

# ==========================================
# 2. LOGIC & CHART LAYER
# Responsibilities: creating specific Plotly figures.
# This makes the main() function much cleaner.
# ==========================================

def create_profit_by_subcategory_chart(df):
    """Generates the Profit by Sub-Category Bar Chart"""
    if df.empty: return None
    
    # Aggregation
    data = df.groupby('Sub-Category')['Profit'].sum().reset_index()
    data = data.sort_values(by='Profit', ascending=False)
    
    # Plotting
    fig = px.bar(data, x='Sub-Category', y='Profit', 
                 title='Profit by Sub-Category', template='plotly_white')
    
    # Styling (Encapsulated here, not in main)
    fig.update_layout(margin=dict(l=20, r=20, t=40, b=20), paper_bgcolor='rgba(0,0,0,0)')
    return fig

def create_top_states_chart(df):
    """Generates the Top 10 States by Sales Chart"""
    if df.empty: return None

    data = df.groupby('State')['Amount'].sum().reset_index()
    data = data.sort_values(by='Amount', ascending=False).head(10)
    
    fig = px.bar(data, x='State', y='Amount', 
                 title='Top 10 States by Sales', template='plotly_white')
    
    fig.update_layout(margin=dict(l=20, r=20, t=40, b=20), paper_bgcolor='rgba(0,0,0,0)')
    fig.update_traces(marker_color='#3b82f6') # Blue
    return fig

def create_top_customers_chart(df):
    """Generates the Top 10 Customers by Sales Chart"""
    if df.empty: return None

    data = df.groupby('CustomerName')['Amount'].sum().reset_index()
    data = data.sort_values(by='Amount', ascending=False).head(10)
    
    fig = px.bar(data, x='CustomerName', y='Amount', 
                 title='Top 10 Customers by Sales', template='plotly_white')
    
    fig.update_layout(margin=dict(l=20, r=20, t=40, b=20), paper_bgcolor='rgba(0,0,0,0)')
    fig.update_traces(marker_color='#10b981') # Green
    return fig

# ==========================================
# 3. UI COMPONENT LAYER (Reusability)
# Responsibilities: Creating repetitive UI elements (like KPI cards)
# ==========================================

def kpi_card(title: str, value: str, icon: str = None):
    """
    A helper to create a consistent KPI card.
    If we want to change the design later, we only change it HERE.
    """
    with ui.card().classes('kpi-card flex-1 min-w-[200px]'):
        ui.label(title).classes('kpi-title')
        ui.label(value).classes('kpi-value')

# ==========================================
# 4. PRESENTATION LAYER (Main Page)
# Responsibilities: Layout and Composition
# ==========================================
@ui.page('/')
def main():
    # --- A. Setup Styles ---
    ui.add_head_html('''
        <style>
            .kpi-card { 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                color: white; 
                border-radius: 8px; 
                padding: 16px; 
                box-shadow: 0 4px 6px rgba(0,0,0,0.1); 
            }
            .kpi-title { font-size: 0.9rem; opacity: 0.9; }
            .kpi-value { font-size: 1.8rem; font-weight: bold; margin-top: 4px; }
            .chart-card { 
                border-radius: 8px; 
                padding: 4px; 
                background: white; 
                box-shadow: 0 2px 4px rgba(0,0,0,0.05); 
                border: 1px solid #eee; 
            }
        </style>
    ''')

    # --- B. Load Data ---
    # We call the data function inside main().
    # This ensures that if the data changes on disk, a page refresh picks it up.
    df = get_sales_data()
    
    if df.empty:
        ui.label("No Data Found").classes("text-red-500 text-xl")
        return

    # --- C. Calculate KPIs ---
    # These are simple scalars, so calculating them inline is fine, 
    # but for complex math, move to a function.
    total_amount = df['Amount'].sum()
    total_profit = df['Profit'].sum()
    total_quantity = df['Quantity'].sum()
    total_orders = df['Order ID'].nunique()

    # --- D. Build Layout ---
    ui.label('📊 Sales Overview').classes('text-2xl font-bold text-center mb-6 text-gray-800')

    # Row 1: KPI Cards
    # Notice how clean this is compared to the original loop/HTML mix
    with ui.row().classes('w-full justify-between gap-4 px-10 mb-8'):
        kpi_card('Total Amount', f'${total_amount:,.0f}')
        kpi_card('Total Profit', f'${total_profit:,.0f}')
        kpi_card('Total Quantity', f'{total_quantity:,}')
        kpi_card('Order Count', f'{total_orders:,}')

    # Row 2: Charts
    # We simply call our "Logic Layer" functions.
    # The layout code doesn't care HOW the chart is made, just WHERE it goes.
    with ui.row().classes('w-full justify-between gap-4 px-10'):
        
        # Chart 1
        with ui.card().classes('chart-card flex-1'):
            fig1 = create_profit_by_subcategory_chart(df)
            ui.plotly(fig1).classes('w-full h-80')

        # Chart 2
        with ui.card().classes('chart-card flex-1'):
            fig2 = create_top_states_chart(df)
            ui.plotly(fig2).classes('w-full h-80')

        # Chart 3
        with ui.card().classes('chart-card flex-1'):
            fig3 = create_top_customers_chart(df)
            ui.plotly(fig3).classes('w-full h-80')

ui.run(title='Sales Dashboard "Pro"', port=8081)
