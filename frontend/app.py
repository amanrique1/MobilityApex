import dash
import requests
from dash import dcc, html, dash_table
import pandas as pd
import plotly.graph_objects as go
from dash.dependencies import Input, Output
import plotly.express as px

# Create Dash app
app = dash.Dash(__name__)

def get_filters_data():
    categories = []
    products = []
    response = requests.get('http://backend:8000/sales/filter_values')
    if response.status_code == 200:
        params_values = response.json()
        categories = params_values['categories']
        products = params_values['products']
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
    return categories, products

def get_aggregated_figs():
    agg_rsp = requests.get('http://backend:8000/sales/category')
    if agg_rsp.status_code == 200:
        agg_data = agg_rsp.json()
        revenue_df = pd.DataFrame(agg_data['revenue'])
        revenue_fig = px.pie(revenue_df, names='category', values='total_sales', hole=0.4, title='Total Revenue by Category')

        avg_price_df = pd.DataFrame(agg_data['mean'])
        avg_price_fig = px.treemap(avg_price_df, path=['category', 'product'], values='price', title='Average Price by Category and Product')

        highest_sales_df = pd.DataFrame(agg_data['day'])
        highest_sales_fig = px.scatter(
            highest_sales_df,
            x="date",
            y="total_sales",
            color="category",
            title="Daily Sales by Category",
            labels={"Sales": "Total Sales", "Date": "Date"}
        )

    return revenue_fig, avg_price_fig, highest_sales_fig


def get_outliers_data():
    outliers_rsp = requests.get('http://backend:8000/sales/outliers')
    if outliers_rsp.status_code == 200:
        outliers = outliers_rsp.json()
        outliers_columns = [{"name": col, "id": col} for col in outliers[0].keys()] if len(outliers) > 0 else []
    return outliers, outliers_columns

categories, products = get_filters_data()
outliers, outliers_columns = get_outliers_data()
revenue_fig, avg_price_fig, highest_sales_day_fig = get_aggregated_figs()


# Define the layout
app.layout = html.Div(children=[
    html.H1(children='Sales Dashboard'),
    
    # Dropdown for selecting category
    dcc.Dropdown(
        id='category-dropdown',
        options=[{'label': 'None', 'value': 'None'}] + [{'label': cat, 'value': cat} for cat in categories if cat is not None],
        value='None',  # Default value
        multi=False,
        placeholder='Select a Category'
    ),
    
    # Dropdown for selecting product name
    dcc.Dropdown(
        id='product-dropdown',
        options=[{'label': 'None', 'value': 'None'}] + [{'label': product, 'value': product} for product in products if product is not None],
        value='None',  # Default value
        multi=False,
        placeholder='Select a Product'
    ),

    dcc.Graph(id='product-sales-plot'),

    dcc.DatePickerRange(
        id="date-picker-range",
        start_date=None,
        end_date=None,
        display_format="YYYY-MM-DD",
        month_format="YYYY-MM",
    ),
    dcc.Graph(id='daily-sales-plot'),

    dcc.Graph(id='avg-price-plot', figure=avg_price_fig),
    dcc.Graph(id='total-revenue-plot', figure=revenue_fig),
    dcc.Graph(id='highest-sales-day-plot', figure=highest_sales_day_fig),


    html.H2("Outliers"),
    dash_table.DataTable(
        id="json-table",
        columns=outliers_columns,          # Define table columns
        data=outliers,           # Pass the JSON data as rows
        filter_action="native",   # Enable filtering
        sort_action="native",     # Enable sorting
        page_action="native",     # Enable pagination
        page_size=5,              # Show 5 rows per page
        style_table={"overflowX": "auto"},
        style_header={"backgroundColor": "rgb(230, 230, 230)", "fontWeight": "bold"},
        style_data={"whiteSpace": "normal", "height": "auto"},
    ) if len(outliers) > 0 else html.H3("No outliers to show")
])

@app.callback(
    Output('product-sales-plot', 'figure'),
    [Input('category-dropdown', 'value'),
     Input('product-dropdown', 'value')]
)
def update_products_plot(selected_category, selected_product):
    # Filter the data based on the selected category and product
    params = {}

    if selected_category != 'None':
        params['category'] = selected_category
    if selected_product != 'None':
        params['product'] = selected_product

    filtered_data = requests.get('http://backend:8000/sales/product', params=params).json()
    filtered_data = pd.DataFrame(filtered_data)
    if filtered_data.empty:
        return {
            'data': [],
            'layout': go.Layout(
                title='No Product Sales for the specified params',
                xaxis={'title': 'Product'},
                yaxis={'title': 'Sales'},
            )
        }
    else:
        # Create the time series plot
        return {
            'data': [
                go.Pie(
                    labels=filtered_data['product'],
                    values=filtered_data['total_sales'],
                    name=f'{selected_category} - {selected_product}' if selected_category != 'None' and selected_product != 'None' else 'Product Sales'
                ),
            ],
            'layout': go.Layout(
                title='Product Sales',
                xaxis={'title': 'Category'},
                yaxis={'title': 'Sales'},
            )
        }

@app.callback(
    Output('daily-sales-plot', 'figure'),
    [Input("date-picker-range", "start_date"),
     Input("date-picker-range", "end_date")]
)
def update_daily_plot(start_date, end_date):
    # Filter the data based on the selected category and product
    params = {}

    if start_date:
        params['start_date'] = start_date
    if end_date:
        params['end_date'] = end_date

    filtered_data = requests.get('http://backend:8000/sales/day', params=params).json()
    filtered_data = pd.DataFrame(filtered_data)
    if filtered_data.empty:
        return {
            'data': [],
            'layout': go.Layout(
                title='No Product Sales on the specified time window',
                xaxis={'title': 'Product'},
                yaxis={'title': 'Sales'},
            )
        }
    else:
        # Create the time series plot
        return {
            'data': [
                go.Scatter(
                    x=filtered_data['date'], 
                    y=filtered_data['total_sales'], 
                    mode='lines+markers', 
                    name=f'{start_date} - {end_date}' if start_date and end_date else 'Daily Sales'
                ),
            ],
            'layout': go.Layout(
                title='Time Series Sales Plot',
                xaxis={'title': 'Date'},
                yaxis={'title': 'Sales'},
            )
        }

# Run the app
if __name__ == '__main__':
    app.run_server(host='0.0.0.0', debug=True)