"""
3. Real‑Time Quote UI
- Build a UI using Tkinter or Streamlit that:
    Lets you type a ticker (AAPL, TSLA, etc.)
- Displays:
    Current bid, Current ask, Last trade price
- Updates automatically as new quotes arrive
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
from alpaca.data.timeframe import TimeFrame
from alpaca_connector import AlpacaConnector


def initialize_session_state():
    if 'connector' not in st.session_state:
        try:
            st.session_state.connector = AlpacaConnector()
            st.session_state.initialized = True
        except Exception as e:
            st.session_state.initialized = False
            st.session_state.error = str(e)

    if 'current_symbol' not in st.session_state:
        st.session_state.current_symbol = 'AAPL'

    if 'auto_refresh' not in st.session_state:
        st.session_state.auto_refresh = True

"""
make a mini candlestick chart for display.
"""
def create_mini_chart(df: pd.DataFrame, symbol: str):
    fig = go.Figure()

    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df['open'],
        high=df['high'],
        low=df['low'],
        close=df['close'],
        name='Price',
        increasing_line_color='#1f77b4',
        decreasing_line_color='#ff7f0e',
        increasing_fillcolor='#1f77b4',
        decreasing_fillcolor='#ff7f0e'
    ))

    fig.update_layout(
        title=f'{symbol} - Historical Price Data',
        title_font=dict(size=18, color='#1e3a8a'),
        yaxis_title='Price ($)',
        xaxis_title='Time',
        height=400,
        margin=dict(l=50, r=50, t=50, b=50),
        hovermode='x unified',
        template='plotly_white',
        xaxis_rangeslider_visible=False,
        paper_bgcolor='white',
        plot_bgcolor='#f0f9ff',
        font=dict(color='#1e3a8a')
    )

    return fig

# vol bar chart
def create_volume_chart(df: pd.DataFrame):
    colors = ['#1f77b4' if df.iloc[i]['close'] >= df.iloc[i]['open']
              else '#ff7f0e' for i in range(len(df))]

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=df.index,
        y=df['volume'],
        marker_color=colors,
        name='Volume',
        opacity=0.7
    ))

    fig.update_layout(
        title='Trading Volume',
        title_font=dict(size=18, color='#1e3a8a'),
        yaxis_title='Volume',
        xaxis_title='Time',
        height=250,
        margin=dict(l=50, r=50, t=50, b=50),
        template='plotly_white',
        showlegend=False,
        paper_bgcolor='white',
        plot_bgcolor='#f0f9ff',
        font=dict(color='#1e3a8a')
    )

    return fig

# display metric card for quote data
def display_quote_card(label: str, value: float, size: int = None, color: str = "blue"):
    if size is not None:
        st.metric(
            label=label,
            value=f"${value:.2f}",
            delta=f"{size:,} shares"
        )
    else:
        st.metric(
            label=label,
            value=f"${value:.2f}"
        )


def main():
    # page config
    st.set_page_config(
        page_title="Alpaca Market Data Terminal",
        page_icon="",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Custom CSS for blue and white theme + custom font
    st.markdown("""
        <style>
        /* Import rounded font from Google Fonts */
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');

        /* Apply rounded font globally */
        * {
            font-family: 'Poppins', sans-serif !important;
        }

        /* Main background */
        .main {
            background-color: #ffffff;
        }

        /* Sidebar styling */
        [data-testid="stSidebar"] {
            background-color: #f0f9ff;
        }

        /* Header styling */
        h1 {
            color: #1e3a8a;
            font-weight: 600;
        }

        h2, h3 {
            color: #2563eb;
            font-weight: 500;
        }

        /* Metric cards */
        [data-testid="stMetricValue"] {
            color: #1e40af;
            font-size: 24px;
            font-weight: 600;
        }

        [data-testid="stMetricLabel"] {
            color: #3b82f6;
            font-weight: 500;
        }

        /* Button styling */
        .stButton>button {
            background-color: #3b82f6;
            color: white;
            border: none;
            border-radius: 10px;
            font-weight: 500;
        }

        .stButton>button:hover {
            background-color: #2563eb;
        }

        /* Input fields */
        .stTextInput>div>div>input {
            border-color: #93c5fd;
            border-radius: 8px;
            font-weight: 400;
        }

        /* Divider */
        hr {
            border-color: #bfdbfe;
        }

        /* Expander */
        [data-testid="stExpander"] {
            border-radius: 8px;
        }
        </style>
    """, unsafe_allow_html=True)

    # Initialize session state
    initialize_session_state()

    # Header
    st.title("Mini Market Data Terminal")
    st.markdown("**Real-time market data powered by Alpaca**")

    # Check if connector is initialized
    if not st.session_state.get('initialized', False):
        st.error("Failed to initialize Alpaca connector")
        st.error(f"Error: {st.session_state.get('error', 'Unknown error')}")
        st.info("Please check your .env file and ensure ALPACA_API_KEY and ALPACA_SECRET_KEY are set correctly.")
        return

    # Sidebar
    with st.sidebar:
        st.header("Settings")

        # Symbol input
        symbol_input = st.text_input(
            "Enter Ticker Symbol",
            value=st.session_state.current_symbol,
            max_chars=10
        ).upper()

        if symbol_input != st.session_state.current_symbol:
            st.session_state.current_symbol = symbol_input

        st.divider()

        # Refresh settings
        st.subheader("Refresh Settings")
        auto_refresh = st.checkbox(
            "Auto-refresh",
            value=st.session_state.auto_refresh
        )
        st.session_state.auto_refresh = auto_refresh

        if auto_refresh:
            refresh_interval = st.slider(
                "Refresh interval (seconds)",
                min_value=1,
                max_value=30,
                value=5
            )
        else:
            refresh_interval = None

        if st.button("Refresh Now", use_container_width=True):
            st.rerun()

        st.divider()

        # Data range settings
        st.subheader("Historical Data")
        data_days = st.selectbox(
            "Time Range",
            options=[1, 3, 7, 14, 30],
            index=0,
            format_func=lambda x: f"{x} day{'s' if x > 1 else ''}"
        )

        timeframe_options = {
            "1 Minute": TimeFrame.Minute,
            "5 Minutes": TimeFrame(5, "Min"),
            "15 Minutes": TimeFrame(15, "Min"),
            "1 Hour": TimeFrame.Hour
        }

        timeframe_label = st.selectbox(
            "Timeframe",
            options=list(timeframe_options.keys()),
            index=0
        )
        timeframe = timeframe_options[timeframe_label]

    # Main content
    connector = st.session_state.connector
    symbol = st.session_state.current_symbol

    # Create columns for layout
    col1, col2, col3, col4 = st.columns(4)

    try:
        # Fetch latest quote
        with st.spinner(f"Fetching data for {symbol}..."):
            quote = connector.get_latest_quote(symbol)

        # Display quote data
        with col1:
            display_quote_card(
                "Bid Price",
                quote['bid_price'],
                quote['bid_size'],
                "blue"
            )

        with col2:
            display_quote_card(
                "Ask Price",
                quote['ask_price'],
                quote['ask_size'],
                "green"
            )

        with col3:
            spread = quote['ask_price'] - quote['bid_price']
            st.metric(
                label="Spread",
                value=f"${spread:.2f}",
                delta=f"{(spread / quote['bid_price'] * 100):.2f}%"
            )

        with col4:
            mid_price = (quote['bid_price'] + quote['ask_price']) / 2
            st.metric(
                label="Mid Price",
                value=f"${mid_price:.2f}"
            )

        # Last update time
        st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        st.divider()

        # DISPLAY ALL HISTORICAL OHLCV DATA
        with st.spinner(f"Loading {data_days}-day chart..."):
            df = connector.get_historical_bars(
                symbol,
                days=data_days,
                timeframe=timeframe
            )

        # Display charts
        if not df.empty:
            # Price chart
            st.plotly_chart(
                create_mini_chart(df, symbol),
                use_container_width=True
            )

            # Volume chart
            st.plotly_chart(
                create_volume_chart(df),
                use_container_width=True
            )

            # Data statistics
            with st.expander("View Statistics"):
                stat_col1, stat_col2, stat_col3 = st.columns(3)

                with stat_col1:
                    st.metric("High", f"${df['high'].max():.2f}")
                    st.metric("Low", f"${df['low'].min():.2f}")

                with stat_col2:
                    st.metric("Average", f"${df['close'].mean():.2f}")
                    st.metric("Latest Close", f"${df['close'].iloc[-1]:.2f}")

                with stat_col3:
                    total_volume = df['volume'].sum()
                    avg_volume = df['volume'].mean()
                    st.metric("Total Volume", f"{total_volume:,.0f}")
                    st.metric("Avg Volume", f"{avg_volume:,.0f}")

            # Recent data table
            with st.expander("View Recent Bars"):
                display_df = df[['open', 'high', 'low', 'close', 'volume']].tail(10)
                display_df = display_df.sort_index(ascending=False)
                st.dataframe(display_df, use_container_width=True)

        else:
            st.warning(f"No historical data available for {symbol}")

    except Exception as e:
        st.error(f"Error fetching data: {str(e)}")
        st.exception(e)

    # Auto-refresh logic
    if auto_refresh and refresh_interval:
        time.sleep(refresh_interval)
        st.rerun()


if __name__ == "__main__":
    main()
