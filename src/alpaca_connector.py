"""
1. Data Connector Module
- Loads API keys from environment variables
- Connects to Alpaca's Market Data API
- Downloads historical data for a symbol you choose
- Streams real time quotes (bid/ask)
"""

import os
from datetime import datetime, timedelta
from typing import Optional, Callable
import pandas as pd
from dotenv import load_dotenv
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.live import StockDataStream
from alpaca.data.requests import StockBarsRequest, StockQuotesRequest
from alpaca.data.timeframe import TimeFrame

"""
Connector class for Alpaca Market Data API.
"""
class AlpacaConnector:
    def __init__(self):
        # load api variables from env
        load_dotenv()
        self.api_key = os.getenv('ALPACA_API_KEY')
        self.secret_key = os.getenv('ALPACA_SECRET_KEY')

        if not self.api_key or not self.secret_key:
            raise ValueError(
                "missing api key"
            )

        # initialize historical data client
        self.historical_client = StockHistoricalDataClient(
            self.api_key,
            self.secret_key
        )

        # initialize streaming client
        self.stream_client = StockDataStream(
            self.api_key,
            self.secret_key
        )

    # retrieve historical OHLCV bar data
    # symbol: stock ticker, days: # of days to retrieve, timeframe: bar time frame
    def get_historical_bars(
        self,
        symbol: str,
        days: int = 30,
        timeframe: TimeFrame = TimeFrame.Minute) -> pd.DataFrame:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        request_params = StockBarsRequest(
            symbol_or_symbols=symbol,
            timeframe=timeframe,
            start=start_date,
            end=end_date
        )

        print(f"fetching {days} days of {timeframe} data for {symbol}...")
        bars = self.historical_client.get_stock_bars(request_params)

        df = bars.df

        if df.empty:
            raise ValueError(f"no data retrieved for {symbol}")

        # Reset index to get symbol and timestamp as columns
        df = df.reset_index()

        # Set timestamp as index
        if 'timestamp' in df.columns:
            df.set_index('timestamp', inplace=True)

        print(f"Retrieved {len(df)} bars for {symbol}")
        return df

    # get the latest quote for a symnbol
    def get_latest_quote(self, symbol: str) -> dict:
        request_params = StockQuotesRequest(
            symbol_or_symbols=symbol,
            limit=1
        )

        quotes = self.historical_client.get_stock_quotes(request_params)
        df = quotes.df

        if df.empty:
            return {
                'bid_price': 0.0,
                'ask_price': 0.0,
                'bid_size': 0,
                'ask_size': 0,
                'timestamp': None
            }

        latest = df.iloc[-1]
        return {
            'bid_price': latest['bid_price'],
            'ask_price': latest['ask_price'],
            'bid_size': latest['bid_size'],
            'ask_size': latest['ask_size'],
            'timestamp': latest.name[1] if isinstance(latest.name, tuple) else latest.name
        }

    # stream real time quotes for a symbol
    async def stream_quotes(
        self,
        symbol: str,
        callback: Callable
    ):
        async def quote_handler(data):
            """Handle incoming quote data"""
            quote_data = {
                'symbol': data.symbol,
                'bid_price': data.bid_price,
                'ask_price': data.ask_price,
                'bid_size': data.bid_size,
                'ask_size': data.ask_size,
                'timestamp': data.timestamp
            }
            await callback(quote_data)

        # Subscribe to quotes for the symbol
        self.stream_client.subscribe_quotes(quote_handler, symbol)

        print(f"✓ Streaming quotes for {symbol}...")
        await self.stream_client._run_forever()

    # streaming real time trades for a symbol
    async def stream_trades(
        self,
        symbol: str,
        callback: Callable
    ):
        async def trade_handler(data):
            """Handle incoming trade data"""
            trade_data = {
                'symbol': data.symbol,
                'price': data.price,
                'size': data.size,
                'timestamp': data.timestamp
            }
            await callback(trade_data)

        # Subscribe to trades for the symbol
        self.stream_client.subscribe_trades(trade_handler, symbol)

        print(f"Streaming trades for {symbol}...")
        await self.stream_client._run_forever()


def test_connector():
    """Test the AlpacaConnector functionality"""
    try:
        # Initialize connector
        connector = AlpacaConnector()

        # Test historical data retrieval
        symbol = 'AAPL'
        print(f"\nTesting historical data for {symbol}...")
        df = connector.get_historical_bars(symbol, days=7, timeframe=TimeFrame.Minute)
        print(f"\nFirst 5 bars:\n{df.head()}")
        print(f"\nLast 5 bars:\n{df.tail()}")

        # Test latest quote
        print(f"\nTesting latest quote for {symbol}...")
        quote = connector.get_latest_quote(symbol)
        print(f"Latest quote: {quote}")

        print("\nll tests passed!")

    except Exception as e:
        print("error")


if __name__ == "__main__":
    test_connector()
