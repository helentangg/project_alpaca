# Mini Market Data Terminal Using Alpaca

## Features

- **Alpaca API Integration**
- **Historical Data**: Download 30+ days of OHLCV data with multiple timeframes
- **Real-Time Quotes**: Display live bid/ask prices and spreads
- **Interactive UI**: Streamlit terminal with auto-refresh
- **OHLCV Visualization**: Candlestick charts and volume analysis

### run the Market Data Terminal

```bash
streamlit run src/realtime_ui.py
```
## Features Implemented

### 1. Data Connector Module (`alpaca_connector.py`)
- Loads API keys from environment variables
- Downloads historical OHLCV data
- Retrieves bid ask

### 2. Real-Time Quote UI (`realtime_ui.py`)
- Ticker symbol input
- Displays historical data:
- Auto-refresh functionality
- Historical candlestick charts
- Volume analysis