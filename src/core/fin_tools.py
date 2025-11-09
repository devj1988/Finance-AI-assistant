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