from langchain.tools import tool
from langchain.agents.middleware import wrap_tool_call
from langchain_core.messages import ToolMessage
import yfinance as yf
import json


@tool
def get_ticker_info(ticker: str) -> str:
    """
    Fetches basic information about a stock ticker using yfinance.
    Args:
        ticker: The stock ticker symbol to fetch information for.
    """
    print("Fetching info for ticker:", ticker)
    try:
        stock = yf.Ticker(ticker)
        return json.dumps(stock.info, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})
    

def filter_news(news_list, company_name, ticker):
    """Filter news articles relevant to the company name or ticker."""
    filtered = []
    for a in news_list:
        article = a['content']
        title = article.get('title', '').lower()
        if company_name.lower() in title or ticker.lower() in title:
            filtered.append({
                "title": article.get("title"),
                "url": article.get("canonicalUrl"),
            })
    return filtered


@tool
def yf_snapshot(ticker: str) -> dict:
    """Return a combined yfinance snapshot for a given ticker."""
    print("Fetching yf_snapshot for ticker:", ticker)
    t = yf.Ticker(ticker)
    info = t.get_info() if hasattr(t, "get_info") else t.info
    history = t.history(period="6mo", interval="1d").tail(120).reset_index().to_dict(orient="list")
    fast = getattr(t, "fast_info", {})
    news = filter_news(t.news, info.get("displayName", ""), ticker)
    out = {
        "ticker": ticker.upper(),
        "info": info,
        "fast_info": dict(fast) if fast is not None else {},
        # "history_6m": history,
        "news": news
    }
    return out
    

# print("yf_snapshot tool loaded for ticker:", yf_snapshot.invoke("AAPL").content)


def yf_news(ticker: str) -> list:
    """Fetch latest news articles for a given ticker."""
    print("Fetching yf_news for ticker:", ticker)
    t = yf.Ticker(ticker)
    news = t.news
    for a in news:
        article = a['content']
        # print(f"Title: {article.get('title')}\nLink: {article.get('link')}\nPublished: {article.get('providerPublishTime')}\n")
    return news

# print("yf_news tool loaded for ticker:", yf_news("AAPL"))

# print("yf_snapshot tool loaded for ticker:", yf_snapshot.invoke("AAPL"))

@tool
def enhance_portfolio_data(portfolio_json: str) -> str:
    """
    Enhances portfolio data by fetching additional information for each ticker.
    Args:
        portfolio_json: JSON string representing the portfolio.
    """
    try:
        portfolio = json.loads(portfolio_json)
        print("portfolio:", portfolio)
        enhanced_holdings = []
        total_value = 0
        for item in portfolio.get("holdings", []):
            total_value += item.get("current_value", 0)
        for item in portfolio.get("holdings", []):
            ticker = item.get("ticker")
            if ticker:
                stock_info = yf.Ticker(ticker).info
                item["current_value"] =  int(item.get("current_value", 0))
                item["longName"] = stock_info.get("longName", "N/A")
                item["sector"] = stock_info.get("sector", "N/A")
                item["industry"] = stock_info.get("industry", "N/A")
                item["weight_percent"] = round(item.get("current_value", 0) / total_value * 100, 2) if total_value > 0 else 0
                # item["info"] = stock_info
            enhanced_holdings.append(item)
        # print("Total portfolio value:", total_value)
        portfolio['holdings'] = enhanced_holdings
        portfolio['total_value'] = total_value
        return json.dumps(portfolio, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})

# portfolio = {
#         "base_currency": "USD",
#         "holdings": [
#             {
#                 "ticker": "AVGO",
#                 "current_value": 15000
#             },
#             {
#                 "ticker": "VOO",
#                 "current_value": 15000
#             }
#         ]
# }

# import json

# print(enhance_portfolio_data(json.dumps(portfolio, default=str)))



@wrap_tool_call
def handle_tool_errors(request, handler):
    """Handle tool execution errors with custom messages."""
    try:
        return handler(request)
    except Exception as e:
        # Return a custom error message to the model
        return ToolMessage(
            content=f"Tool error: Please check your input and try again. ({str(e)})",
            tool_call_id=request.tool_call["id"])