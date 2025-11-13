import yfinance as yf
import pprint
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
from typing import Any, Dict

def test_yfinance():
    dat = yf.Ticker("MSFT")
    # hist = dat.history(period="1y")

    # pprint.pprint(dat.info)
    pprint.pprint(dat.fast_info)
    pprint.pprint(dat.news)
    # print(hist)
    # print(f"MSFT closing price on the last day: {hist['Close'][-1]}")


def get_ticker_info(ticker: str) -> Dict[str, Any]:
    """
    Fetches basic information about a stock ticker using yfinance.
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        print
        return {
            "ticker": ticker,
            "longName": info.get("longName", "N/A"),
            "sector": info.get("sector", "N/A"),
            "industry": info.get("industry", "N/A"),
            "marketCap": info.get("marketCap", "N/A"),
            "currentPrice": info.get("currentPrice", "N/A"),
            "previousClose": info.get("previousClose", "N/A"),
            "open": info.get("open", "N/A"),
            "dayHigh": info.get("dayHigh", "N/A"),
            "dayLow": info.get("dayLow", "N/A"),
        }
    except Exception as e:
        return {"error": str(e)}
    
def test_market_info():    
    US = yf.Market("US")

    status = US.status
    summary = US.summary

    pprint.pprint(status)
    pprint.pprint(summary)

# test_yfinance()

def yf_snapshot(ticker: str) -> dict:
    """Return a combined yfinance snapshot for a given ticker."""
    print("Fetching yf_snapshot for ticker:", ticker)
    t = yf.Ticker(ticker)
    info = t.get_info() if hasattr(t, "get_info") else t.info
    history = t.history(period="6mo", interval="1d").tail(120).reset_index().to_dict(orient="list")
    fast = getattr(t, "fast_info", {})
    out = {
        # "ticker": ticker.upper(),
        # "info": info,
        # "fast_info": dict(fast) if fast is not None else {},
        "history_6m": history,
    }
    return out

def plot_price_history(history_data: dict, ticker: str = "Stock", show_volume: bool = False):
    """
    Creates a matplotlib chart from 6-month history data.
    
    Args:
        history_data: Dictionary containing Date, Close, Volume, etc. from yf_snapshot
        ticker: Stock ticker symbol for chart title
        show_volume: Whether to show volume subplot
    """
    # Extract data from the history dictionary
    dates = history_data.get('Date', [])
    closes = history_data.get('Close', [])
    volumes = history_data.get('Volume', [])
    opens = history_data.get('Open', [])
    highs = history_data.get('High', [])
    lows = history_data.get('Low', [])
    
    if not dates or not closes:
        print("Error: No date or close price data found")
        return
    
    # Convert dates to datetime objects if they're not already
    if dates and hasattr(dates[0], 'date'):
        dates = [d.date() if hasattr(d, 'date') else d for d in dates]
    
    # Create the plot
    if show_volume and volumes:
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), height_ratios=[3, 1])
        
        # Price chart
        ax1.plot(dates, closes, linewidth=2, color='blue', label='Close Price')
        ax1.fill_between(dates, lows, highs, alpha=0.3, color='lightblue', label='Daily Range')
        ax1.set_title(f'{ticker} - 6 Month Price History', fontsize=16, fontweight='bold')
        ax1.set_ylabel('Price ($)', fontsize=12)
        ax1.grid(True, alpha=0.3)
        ax1.legend()
        
        # Volume chart
        ax2.bar(dates, volumes, alpha=0.7, color='orange')
        ax2.set_title('Trading Volume', fontsize=12)
        ax2.set_ylabel('Volume', fontsize=12)
        ax2.set_xlabel('Date', fontsize=12)
        ax2.grid(True, alpha=0.3)
        
        # Format x-axis dates for both subplots
        for ax in [ax1, ax2]:
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            ax.xaxis.set_major_locator(mdates.MonthLocator())
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
    else:
        # Single price chart
        fig, ax1 = plt.subplots(figsize=(12, 6))
        ax1.plot(dates, closes, linewidth=2, color='blue', label='Close Price')
        if highs and lows:
            ax1.fill_between(dates, lows, highs, alpha=0.3, color='lightblue', label='Daily Range')
        
        ax1.set_title(f'{ticker} - 6 Month Price History', fontsize=16, fontweight='bold')
        ax1.set_ylabel('Price ($)', fontsize=12)
        ax1.set_xlabel('Date', fontsize=12)
        ax1.grid(True, alpha=0.3)
        ax1.legend()
        
        # Format x-axis dates
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax1.xaxis.set_major_locator(mdates.MonthLocator())
        plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)
    
    plt.tight_layout()
    plt.show()

def plot_snapshot_chart(ticker: str, show_volume: bool = False):
    """
    Convenience function that fetches data and creates chart in one step.
    
    Args:
        ticker: Stock ticker symbol
        show_volume: Whether to show volume subplot
    """
    snapshot = yf_snapshot(ticker)
    history_6m = snapshot["history_6m"]
    plot_price_history(history_6m, ticker.upper(), show_volume)

# snapshot = yf_snapshot("AAPL")
# history_6m = snapshot["history_6m"]
# print("AAPL 6 month history sample:", history_6m['Close'][-1])
# print("AAPL 6 month history sample dates:", history_6m['Date'][-1].date())

plot_snapshot_chart