import pandas as pd
import dash
import dash_bootstrap_components as dbc
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import threading
import queue
import time
from datetime import datetime
import numpy as np
import signal
import sys
from consumer import BitcoinDataConsumer

# Initialize the consumer
data_consumer = BitcoinDataConsumer()

# Start consumer in a separate thread
consumer_thread = threading.Thread(target=data_consumer.start_consuming, daemon=True)
consumer_thread.start()

# Custom CSS for better styling
external_stylesheets = [
    'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css',
    dbc.themes.BOOTSTRAP
]

# Initialize Dash App
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

# Colors and Theme
COLORS = {
    'background': '#0a0f1c',  # Dark blue-black
    'card_bg': '#151c2c',     # Slightly lighter blue-black
    'primary': '#3861fb',     # Bright blue
    'secondary': '#1fcff1',   # Light blue
    'accent': '#f7931a',      # Bitcoin orange
    'text': '#ffffff',        # White
    'text_secondary': '#7a859d',  # Muted text
    'positive': '#00c853',    # Green
    'negative': '#ff1744',    # Red
    'border': '#232d3f'       # Border color
}

# Custom CSS Styles
custom_styles = {
    'card': {
        'backgroundColor': COLORS['card_bg'],
        'borderRadius': '12px',
        'boxShadow': '0 4px 6px rgba(0, 0, 0, 0.1)',
        'padding': '20px',
        'margin': '10px',
        'border': f'1px solid {COLORS["border"]}'
    },
    'gradient_card': {
        'background': f'linear-gradient(145deg, {COLORS["card_bg"]}, {COLORS["background"]})',
        'borderRadius': '12px',
        'boxShadow': '0 4px 6px rgba(0, 0, 0, 0.1)',
        'padding': '20px',
        'margin': '10px',
        'border': f'1px solid {COLORS["border"]}'
    }
}

# Layout
app.layout = html.Div([
    # Navigation Bar
    html.Div([
        html.Div([
            html.I(className="fab fa-bitcoin fa-3x",
                  style={'color': COLORS['accent'], 'marginRight': '10px'}),
            html.H1('Bitcoin Analytics Dashboard',
                   style={'color': COLORS['text'], 'margin': '0', 'fontSize': '32px', 'fontWeight': 'bold'})
        ], style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center', 'flex': '1'}),

        html.Div([
            html.Span('Last Updated: ', style={'color': COLORS['text_secondary'], 'marginRight': '5px'}),
            html.Span(id='last-update', style={'color': COLORS['text']})
        ], style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'flex-end', 'marginRight': '20px'})
    ], style={
        'display': 'flex',
        'justifyContent': 'space-between',
        'alignItems': 'center',
        'padding': '20px',
        'backgroundColor': COLORS['card_bg'],
        'marginBottom': '20px',
        'borderRadius': '12px',
        'border': f'1px solid {COLORS["border"]}',
        'boxShadow': '0 4px 6px rgba(0, 0, 0, 0.1)'
    }),

    # Main Content
    html.Div([
        # Left Column - Main Charts
        html.Div([
            # Price Overview Card
            html.Div([
                html.Div([
                    html.H2('Bitcoin Price Overview',
                            style={'color': COLORS['text'], 'marginBottom': '20px', 'textAlign': 'center'}),
                    html.Div([
                        html.Div([
                            html.Span('Current Price',
                                    style={'color': COLORS['text_secondary'], 'display': 'block', 'textAlign': 'center'}),
                            html.H3(id='current-price',
                                    style={'color': COLORS['text'], 'margin': '10px 0', 'textAlign': 'center'})
                        ], style={'flex': '1', 'textAlign': 'center'}),
                        html.Div([
                            html.Span('24h Change',
                                    style={'color': COLORS['text_secondary'], 'display': 'block', 'textAlign': 'center'}),
                            html.H3(id='price-change',
                                    style={'margin': '10px 0', 'textAlign': 'center'})
                        ], style={'flex': '1', 'textAlign': 'center'}),
                        html.Div([
                            html.Span('Volume',
                                    style={'color': COLORS['text_secondary'], 'display': 'block', 'textAlign': 'center'}),
                            html.H3(id='current-volume',
                                    style={'color': COLORS['text'], 'margin': '10px 0', 'textAlign': 'center'})
                        ], style={'flex': '1', 'textAlign': 'center'})
                    ], style={'display': 'flex', 'gap': '20px', 'justifyContent': 'center'})
                ], style=custom_styles['gradient_card'])
            ], style={'marginBottom': '20px'}),

            # Date Range Selector
            html.Div([
                dcc.DatePickerRange(
                    id='date-picker-range',
                    start_date=datetime.now().date(),
                    end_date=datetime.now().date(),
                    display_format='YYYY-MM-DD',
                )
            ], style={'padding': '10px', 'backgroundColor': '#151c2c', 'borderRadius': '12px', 'border': f'1px solid {"#151c2c"}'}),

            # Main Chart
            html.Div([
                dcc.Graph(id='combined-chart')
            ], style=custom_styles['card']),

            # Technical Indicators
            html.Div([
                html.Div([
                    dcc.Graph(id='technical-indicators')
                ], style={'flex': '1'}),
                html.Div([
                    dcc.Graph(id='rsi-chart')
                ], style={'flex': '1'})
            ], style={
                'display': 'flex',
                'gap': '20px',
                'marginTop': '20px'
            })
        ], className='eight columns', style={'padding': '10px'}),

        # Right Column - Analytics & Stats
        html.Div([
            # Market Status Card
            html.Div([
                html.Div([
                    html.H3('Market Status',
                           style={'color': COLORS['text'], 'marginBottom': '10px'}),
                    html.Div(id='market-status',
                            style={'fontSize': '20px', 'color': COLORS['positive']})
                ], style=custom_styles['gradient_card'])
            ], style={'marginBottom': '20px'}),

            # Price Distribution
            html.Div([
                dcc.Graph(id='price-distribution')
            ], style=custom_styles['card']),

            # Recent Trades Table
            html.Div([
                html.H3('Recent Trades',
                       style={'color': COLORS['text'], 'marginBottom': '15px'}),
                html.Div(id='recent-trades-table',
                        style={
                            'maxHeight': '400px',
                            'overflow': 'auto',
                            'borderRadius': '8px',
                            'border': f'1px solid {COLORS["border"]}'
                        })
            ], style=custom_styles['card'])
        ], className='four columns', style={'padding': '10px'})
    ], className='row'),

    # Footer
    html.Div([
        html.Div([
            html.Span('Bitcoin Analytics Dashboard',
                     style={'color': COLORS['text_secondary']}),
            html.Span('Real-Time Data',
                     style={'color': COLORS['accent']})
        ], style={'display': 'flex', 'justifyContent': 'space-between'})
    ], style={
        'marginTop': '20px',
        'padding': '20px',
        'backgroundColor': COLORS['card_bg'],
        'borderRadius': '12px',
        'border': f'1px solid {COLORS["border"]}'
    }),

    # Export Options
    html.Div([
        dbc.Button("Export Data", id="export-button", color="primary", className="me-1", style={
            'margin': '20px 0',
            'display': 'inline-block',
            'padding': '10px 20px',
            'fontSize': '16px',
            'fontWeight': 'bold',
            'borderRadius': '8px',
            'boxShadow': '0 4px 6px rgba(0, 0, 0, 0.1)',
            'transition': 'background-color 0.3s ease, box-shadow 0.3s ease'
        }),
        dcc.Download(id="download-dataframe-csv")
    ], style={
        'padding': '20px',
        'backgroundColor': COLORS['card_bg'],
        'borderRadius': '12px',
        'border': f'1px solid {COLORS["border"]}',
        'boxShadow': '0 4px 6px rgba(0, 0, 0, 0.1)',
        'display': 'flex',
        'alignItems': 'center',
        'justifyContent': 'flex-start'
    }),

    dcc.Interval(
        id='interval-component',
        interval=1*1000,
        n_intervals=0
    )
], style={
    'backgroundColor': COLORS['background'],
    'minHeight': '100vh',
    'padding': '20px',
    'fontFamily': '"Inter", system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif'
})

# Add custom CSS to index
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>Bitcoin Analytics</title>
        {%favicon%}
        {%css%}
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }

            ::-webkit-scrollbar {
                width: 8px;
                height: 8px;
            }

            ::-webkit-scrollbar-track {
                background: #151c2c;
                border-radius: 4px;
            }

            ::-webkit-scrollbar-thumb {
                background: #3861fb;
                border-radius: 4px;
            }

            ::-webkit-scrollbar-thumb:hover {
                background: #1fcff1;
            }

            .stats-card {
                transition: transform 0.2s ease, box-shadow 0.2s ease;
            }

            .stats-card:hover {
                transform: translateY(-2px);
                box-shadow: 0 8px 12px rgba(0, 0, 0, 0.2);
            }

            table {
                width: 100%;
                border-collapse: collapse;
            }

            th, td {
                padding: 12px;
                text-align: left;
                border-bottom: 1px solid #232d3f;
            }

            tr:hover {
                background-color: rgba(56, 97, 251, 0.1);
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

# Helper Function: Calculate Technical Indicators
def calculate_technical_indicators(df):
    # Calculate RSI
    delta = df['price'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))

    # Calculate Moving Averages
    df['SMA_20'] = df['price'].rolling(window=20).mean()
    df['SMA_50'] = df['price'].rolling(window=50).mean()

    # Calculate Bollinger Bands
    df['BB_middle'] = df['price'].rolling(window=20).mean()
    df['BB_upper'] = df['BB_middle'] + 2 * df['price'].rolling(window=20).std()
    df['BB_lower'] = df['BB_middle'] - 2 * df['price'].rolling(window=20).std()

    # Calculate MACD
    df['EMA_12'] = df['price'].ewm(span=12, adjust=False).mean()
    df['EMA_26'] = df['price'].ewm(span=26, adjust=False).mean()
    df['MACD'] = df['EMA_12'] - df['EMA_26']
    df['MACD_signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['MACD_hist'] = df['MACD'] - df['MACD_signal']

    return df

# Callback for Updating Dashboard
@app.callback(
    [Output('current-price', 'children'),
     Output('price-change', 'children'),
     Output('price-change', 'style'),
     Output('current-volume', 'children'),
     Output('market-status', 'children'),
     Output('combined-chart', 'figure'),
     Output('technical-indicators', 'figure'),
     Output('rsi-chart', 'figure'),
     Output('price-distribution', 'figure'),
     Output('recent-trades-table', 'children'),
     Output('last-update', 'children')],
    [Input('interval-component', 'n_intervals'),
     Input('date-picker-range', 'start_date'),
     Input('date-picker-range', 'end_date')]
)
def update_dashboard(n_intervals, start_date, end_date):
    # Get latest data from consumer
    price_df = data_consumer.get_latest_data('price', limit=100)
    sma_df = data_consumer.get_latest_data('sma', limit=100)
    bb_df = data_consumer.get_latest_data('bb', limit=100)

    if len(price_df) == 0:
        return "$0.00", "0.00%", {'color': COLORS['text_secondary']}, "$0.00", "N/A", go.Figure(), go.Figure(), go.Figure(), go.Figure(), ""

    # Filter data based on date range
    if start_date and end_date:
        price_df = price_df[(price_df['date'] >= start_date) & (price_df['date'] <= end_date)]
        sma_df = sma_df[(sma_df['window_start'] >= start_date) & (sma_df['window_start'] <= end_date)]
        bb_df = bb_df[(bb_df['window_start'] >= start_date) & (bb_df['window_start'] <= end_date)]

    # Current values
    current_price = f"${price_df['price'].iloc[-1]:,.2f}"
    price_change = price_df['change_percent'].iloc[-1]
    change_style = {'color': COLORS['positive'] if price_change >= 0 else COLORS['negative']}
    current_volume = f"${price_df['volume'].iloc[-1]:,.2f}"
    market_status = "Bullish" if price_change >= 0 else "Bearish"

    # Combined Chart
    combined_fig = go.Figure()
    combined_fig.add_trace(go.Scatter(x=pd.to_datetime(price_df['timestamp']), y=price_df['price'], name="Price", line=dict(color=COLORS['accent'])))
    combined_fig.update_layout(template="plotly_dark", paper_bgcolor=COLORS['background'], hovermode='x unified')

    # Technical Indicators
    technical_fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.1,
                                   subplot_titles=('Moving Averages & Bollinger Bands', 'MACD'))

    # Moving Averages and Bollinger Bands
    technical_fig.add_trace(go.Scatter(x=pd.to_datetime(sma_df['window_start']), y=sma_df['sma_20'], name="SMA 20", line=dict(color=COLORS['primary'])), row=1, col=1)
    technical_fig.add_trace(go.Scatter(x=pd.to_datetime(bb_df['window_start']), y=bb_df['bb_upper'], name="BB Upper", line=dict(color=COLORS['accent'], dash='dash')), row=1, col=1)
    technical_fig.add_trace(go.Scatter(x=pd.to_datetime(bb_df['window_start']), y=bb_df['bb_middle'], name="BB Middle", line=dict(color=COLORS['accent'], dash='dot')), row=1, col=1)
    technical_fig.add_trace(go.Scatter(x=pd.to_datetime(bb_df['window_start']), y=bb_df['bb_lower'], name="BB Lower", line=dict(color=COLORS['accent'], dash='dash')), row=1, col=1)

    # MACD
    technical_fig.add_trace(go.Scatter(x=pd.to_datetime(price_df['timestamp']), y=price_df['price'].ewm(span=12, adjust=False).mean() - price_df['price'].ewm(span=26, adjust=False).mean(), name="MACD", line=dict(color=COLORS['primary'])), row=2, col=1)
    technical_fig.add_trace(go.Scatter(x=pd.to_datetime(price_df['timestamp']), y=(price_df['price'].ewm(span=12, adjust=False).mean() - price_df['price'].ewm(span=26, adjust=False).mean()).ewm(span=9, adjust=False).mean(), name="MACD Signal", line=dict(color=COLORS['secondary'])), row=2, col=1)
    technical_fig.add_trace(go.Bar(x=pd.to_datetime(price_df['timestamp']), y=(price_df['price'].ewm(span=12, adjust=False).mean() - price_df['price'].ewm(span=26, adjust=False).mean()) - (price_df['price'].ewm(span=12, adjust=False).mean() - price_df['price'].ewm(span=26, adjust=False).mean()).ewm(span=9, adjust=False).mean(), name="MACD Histogram", marker_color=COLORS['accent']), row=2, col=1)

    technical_fig.update_layout(template="plotly_dark", paper_bgcolor=COLORS['background'], hovermode='x unified')

    # RSI Chart
    rsi_fig = go.Figure()
    rsi_fig.add_trace(go.Scatter(x=pd.to_datetime(price_df['timestamp']), y=price_df['price'].rolling(window=14).apply(lambda x: 100 - (100 / (1 + (x.where(x > 0, 0).mean() / (-x.where(x < 0, 0).mean())))), raw=False), name="RSI", line=dict(color=COLORS['accent'])))
    rsi_fig.update_layout(template="plotly_dark", paper_bgcolor=COLORS['background'], hovermode='x unified')

    # Candlestick Chart
    candlestick_fig = go.Figure(data=[go.Candlestick(x=pd.to_datetime(price_df['timestamp']),
                                                     open=price_df['open'],
                                                     high=price_df['high'],
                                                     low=price_df['low'],
                                                     close=price_df['price'])])
    candlestick_fig.update_layout(template="plotly_dark", paper_bgcolor=COLORS['background'], hovermode='x unified')

    recent_trades_table = html.Div([
        html.Table([
            html.Thead(html.Tr([
                html.Th("Date", style={'color': COLORS['accent'], 'textAlign': 'center'}),
                html.Th("Price", style={'color': COLORS['accent'], 'textAlign': 'center'}),
                html.Th("Volume", style={'color': COLORS['accent'], 'textAlign': 'center'})
            ])),
            html.Tbody([
                html.Tr([
                    html.Td(row['timestamp'].strftime('%Y-%m-%d'), style={'color': COLORS['text'], 'textAlign': 'center'}),
                    html.Td(f"${row['price']:,.2f}", style={'color': COLORS['text'], 'textAlign': 'center'}),
                    html.Td(f"${row['volume']:,.2f}", style={'color': COLORS['text'], 'textAlign': 'center'})
                ]) for row in price_df.iloc[-5:].to_dict('records')
            ])
        ], style={
            'width': '100%',
            'borderCollapse': 'collapse',
            'margin': '0 auto'
        })
    ], style={
        'padding': '20px',
        'backgroundColor': COLORS['card_bg'],
        'borderRadius': '12px',
        'border': f'1px solid {COLORS["border"]}',
        'boxShadow': '0 4px 6px rgba(0, 0, 0, 0.1)',
        'overflow': 'auto',
        'maxHeight': '400px'
    })

    last_update = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return current_price, f"{price_change:+.2f}%", change_style, current_volume, market_status, combined_fig, technical_fig, rsi_fig, candlestick_fig, recent_trades_table, last_update

# Callback for Exporting Data
@app.callback(
    Output("download-dataframe-csv", "data"),
    Input("export-button", "n_clicks"),
    prevent_initial_call=True,
)
def export_data(n_clicks):
    if n_clicks is None:
        return None
    price_df = data_consumer.get_latest_data('price', limit=100)
    return dcc.send_data_frame(price_df.to_csv, "bitcoin_data.csv")

# Signal handler for graceful shutdown
def signal_handler(signal, frame):
    print('Shutting down the server...')
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

# Run App
if __name__ == "__main__":
    app.run_server(debug=True, host='0.0.0.0', port=8051)
