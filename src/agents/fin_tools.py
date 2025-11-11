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
                item["longName"] = stock_info.get("longName", "N/A")
                item["sector"] = stock_info.get("sector", "N/A")
                item["industry"] = stock_info.get("industry", "N/A")
                item["weight_percent"] = round(item.get("current_value", 0) / total_value * 100, 2) if total_value > 0 else 0
            enhanced_holdings.append(item)
        print("Total portfolio value:", total_value)
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