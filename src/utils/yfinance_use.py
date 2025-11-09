import yfinance as yf
import pprint

def test_yfinance():
    dat = yf.Ticker("MSFT")
    # hist = dat.history(period="1y")

    # pprint.pprint(dat.info)
    pprint.pprint(dat.fast_info)
    pprint.pprint(dat.news)
    # print(hist)
    # print(f"MSFT closing price on the last day: {hist['Close'][-1]}")


from typing import Any, Dict

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

test_yfinance()