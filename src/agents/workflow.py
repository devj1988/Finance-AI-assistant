from typing import TypedDict, Annotated, List, Optional
import operator
from langchain_core.messages import BaseMessage
from langchain_core.messages import ToolMessage, HumanMessage
from fin_tools import get_ticker_info, enhance_portfolio_data, yf_snapshot
from retrieval_tool import retrieve_documents
from qa_agent_test import get_qa_agent
from portfolio_insights import get_portfolio_insights_agent
from market_trends import get_market_trends_agent
from goal_planning import get_goal_planning_agent
import json
from model import GoalPlanResult, MarketInsightsResult
from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.memory import InMemorySaver
from cachetools import TTLCache


class MarketTrendsState(TypedDict):
    """State schema for market trends agent"""

    ticker_6mo_price_history: Optional[dict]

    news: Optional[list]

    market_trends: Optional[MarketInsightsResult]

class AssistantState(TypedDict):
    """Simple state schema for multiagent system"""

    # Conversation history - persisted with checkpoint memory
    messages: Annotated[List[BaseMessage], operator.add]

    context: str

    market_trends_ticker: Optional[str]

    portfolio_json: Optional[dict]

    goal_plan_inputs: Optional[dict]

    # Agent routing
    next_agent: Optional[str]

    # Current user goal
    user_goal: Optional[str]

    market_trends_agent_tools_out: Optional[MarketTrendsState]

    goal_planning_output: Optional[GoalPlanResult]


qa_agent = get_qa_agent()

portfolio_agent = get_portfolio_insights_agent()

market_trends_agent = get_market_trends_agent()

goal_planning_agent = get_goal_planning_agent()

goal_planning_agent_cache = TTLCache(maxsize=100, ttl=3600) 

def get_key_for_goal_plan_inputs(inputs: dict) -> str:
    s = "|".join([
        str(inputs.get("goal_type", "")),
        str(inputs.get("goal_target_amount", "")),
        str(inputs.get("goal_target_horizon", "")),
        str(inputs.get("current_net_worth", "")),
        str(inputs.get("risk_tolerance", "")),
        str(inputs.get("current_age", "")),
        str(inputs.get("annual_income", "")),
        str(inputs.get("monthly_expenses", "")),
        str(inputs.get("monthly_savings", ""))
    ])
    print("Generated hash for goal planning inputs:", hash(s))
    return str(hash(s))

def goal_planning_agent_node(state: AssistantState):
    """Goal planning agent node"""
    print("Invoking goal planning agent...")
    # print("goal_plan_inputs:", state["goal_plan_inputs"])

    key = get_key_for_goal_plan_inputs(state["goal_plan_inputs"])
    print("Generated key for goal planning inputs:", key)

    if key in goal_planning_agent_cache:
        print("Using cached goal planning for key:", key)
        return goal_planning_agent_cache[key]

    response = goal_planning_agent.invoke({
            **state["goal_plan_inputs"],
        })
    # print(response)
    ret = {"goal_planning_output": response}
    goal_planning_agent_cache[key] = ret
    return ret

# Agent node functions
def qa_agent_node(state: AssistantState):
    """QA agent node"""
    print("Invoking QA agent...")
    messages = state["messages"]
    response = qa_agent.invoke({"messages": messages})

    print("QA agent response:", response)

    # Handle tool calls if present
    if hasattr(response, 'tool_calls') and response.tool_calls:
        tool_messages = []
        tool_map = {
            "get_ticker_info": get_ticker_info,
            "retrieve_documents": retrieve_documents,
        }
        for tool_call in response.tool_calls:
            if tool_call['name'] in tool_map.keys():
                try:
                    tool_result = tool_map[tool_call['name']].invoke(tool_call)
                except Exception as e:
                    tool_result = f"Search failed: {str(e)}"
                finally:
                    tool_messages.append(tool_result)

        if tool_messages:
            all_messages = messages + [response] + tool_messages
            final_response = qa_agent.invoke({"messages": all_messages})
            print("*"*40)
            print("Final response after tool calls:", final_response)
            print("*"*40)
            return {"messages": [response] + tool_messages + [final_response]}

    return {"messages": [response]}

market_trends_agent_cache = TTLCache(maxsize=100, ttl=3600) 

# Agent node functions
def market_trends_agent_node(state: AssistantState):
    """Market trends agent node"""
    print("Invoking market trends agent...")
    ticker = state["market_trends_ticker"]
    print("market_trends_ticker:", ticker)
    messages = []
    if ticker in market_trends_agent_cache:
        print("Using cached messages for ticker:", ticker)
        return market_trends_agent_cache[ticker]
    
    response = market_trends_agent.invoke({
            "messages": messages,
            "ticker": ticker,
    })

    print("Market trends agent response initial:", response)

    # Handle tool calls if present
    if hasattr(response, 'tool_calls') and response.tool_calls:
        print("Market trends agent tool calls detected:", response.tool_calls)

        tool_messages = []
        tool_map = {
            "yf_snapshot": yf_snapshot,
        }
        ticker_6mo_price_history = {}
        news = []
        for tool_call in response.tool_calls:
            if tool_call['name'] in tool_map.keys():
                try:
                    tool_result = tool_map[tool_call['name']].invoke(tool_call)
                    print(tool_result)
                    if tool_call['name'] == "yf_snapshot" and tool_result:
                        # Store 6 month price history in state
                        # print("tool_result from yf_snapshot:", tool_result)
                        content_json = json.loads(tool_result.content)
                        print("Extracted ticker:", content_json.get('ticker'))
                        ticker_6mo_price_history = content_json.get("history_6m", {})
                        news = content_json.get("news", [])
                        print("Extracted news articles:", news)
                        # tool_result.pop("history_6m", None)
                except Exception as e:
                    tool_result = f"Search failed: {str(e)}"
                finally:
                    tool_messages.append(tool_result)

        if tool_messages:
            all_messages = messages + [response] + tool_messages
            final_response = market_trends_agent.invoke({"messages": all_messages, "ticker": ticker})
            print("*"*40)
            print("Final response after tool calls:", final_response)
            print("*"*40)
            ret = {"messages": [response] + tool_messages + [final_response],
                   "market_trends_agent_tools_out": MarketTrendsState(
                       ticker_6mo_price_history=ticker_6mo_price_history,
                       news=news
                   )
               }
    else:
        ret = {"messages": [response]}

    print("Caching market trends messages for ticker, response  :", ret)
    market_trends_agent_cache[ticker] = ret
    return ret

def get_key(portfolio_json: dict, user_goal: str) -> str:
    """Generate a cache key based on portfolio and user goal"""
    currency = portfolio_json.get("base_currency", "")
    holdings = portfolio_json.get("holdings", [])
    user_goal = user_goal or ""

    holdings.sort(key=lambda x: x.get("ticker", ""))

    portfolio_str = f"{currency}-" + "-".join(
        [f"{item.get('ticker','')}_{item.get('current_value',0)}" for item in holdings]
    )

    print("Generated portfolio string for key:", portfolio_str)
    return f"{portfolio_str}|{user_goal}"


portfolio_agent_cache = TTLCache(maxsize=100, ttl=3600) 

def portfolio_agent_node(state: AssistantState):
    """Portfolio analysis agent node"""
    print("Invoking portfolio agent...")
    # print("portfolio_json:", state["portfolio_json"])
    # print("user_goal:", state["user_goal"])

    key = get_key(state["portfolio_json"], state["user_goal"])

    if key in portfolio_agent_cache:
        print("Using cached portfolio analysis for key:", key)
        return portfolio_agent_cache[key]

    response = portfolio_agent.invoke({
            "portfolio_json": state["portfolio_json"],
            "user_goal": state["user_goal"],
        })
    # print(response)
    portfolio_agent_cache[key] = {"messages": [response]}
    return {"messages": [response]}

def portfolio_enhance_node(state: AssistantState):
    """Portfolio enhancement node"""
    print("Enhancing portfolio data...")
    portfolio_json = state["portfolio_json"]
    enhanced_portfolio_str = enhance_portfolio_data.invoke(json.dumps(portfolio_json, default=str))
    enhanced_portfolio = json.loads(enhanced_portfolio_str)
    # print("enhanced_portfolio:", enhanced_portfolio)
    return {
        "portfolio_json": enhanced_portfolio
    }


def router_node(state: AssistantState):
    """Router node - determines which agent should handle the query"""
    context = state.get("context", "qa")
    print(f"Routing to {context} agent...")
    next_agent = "qa_agent"
    if context == "market_trends":
        next_agent = "market_trends_agent"
    elif context == "portfolio":
        next_agent = "portfolio_enhance"
    elif context == "goals_planning":
        next_agent = "goals_planning_agent"
    else:
        next_agent = "qa_agent"

    return {
        "next_agent": next_agent
    }

def route_to_agent(state: AssistantState):
    """Conditional edge function - routes to appropriate agent based on router decision"""

    next_agent = state.get("next_agent")

    if next_agent == "qa_agent":
        return "qa_agent"
    elif next_agent == "portfolio_enhance":
        return "portfolio_enhance"
    elif next_agent == "market_trends_agent":
        return "market_trends_agent"
    elif next_agent == "goals_planning_agent":
        return "goals_planning_agent"
    else:
        # Default fallback
        return "qa_agent"
    

from IPython.display import Image
import io
from PIL import Image as PILImage # Alias to avoid name collision


def save_ipython_image(img_display: Image, filename: str):
    """Saves an IPython display Image to a file using Pillow."""
    # Assume 'img_display' is an IPython.core.display.Image object
    # Read the image data and save it using Pillow
    pimg = PILImage.open(io.BytesIO(img_display.data))
    pimg.save(filename)


def create_workflow():
    checkpointer = InMemorySaver()

    workflow = StateGraph(AssistantState)

    workflow.add_node("router", router_node)
    workflow.add_node("portfolio_agent", portfolio_agent_node)
    workflow.add_node("portfolio_enhance", portfolio_enhance_node)
    workflow.add_node("market_trends_agent", market_trends_agent_node)
    workflow.add_node("goals_planning_agent", goal_planning_agent_node)
    workflow.add_node("qa_agent", qa_agent_node)

    workflow.set_entry_point("router")

    workflow.add_conditional_edges(
        "router",
        route_to_agent,
        {
            "qa_agent": "qa_agent",
            "portfolio_enhance": "portfolio_enhance",
            "market_trends_agent": "market_trends_agent",
            "goals_planning_agent": "goals_planning_agent"
        }
    )

    workflow.add_edge("portfolio_enhance", "portfolio_agent")
    workflow.add_edge("market_trends_agent", END)
    workflow.add_edge("goals_planning_agent", END)
    workflow.add_edge("portfolio_agent", END)
    workflow.add_edge("qa_agent", END)

    app = workflow.compile(checkpointer=checkpointer)

    # save_ipython_image(Image(app.get_graph().draw_mermaid_png()), "workflow_graph.png")

    return app

create_workflow()


# sample_portfolio = {
#         "base_currency": "USD",
#         "horizon_years": 15,
#         "risk_tolerance": "moderate",
#         "holdings": [
#             {
#                 "ticker": "VTI",
#                 "name": "Vanguard Total Stock Market ETF",
#                 "asset_class": "Equity",
#                 "region": "US",
#                 "sector": "Broad Market",
#                 "weight_percent": 50.0,
#                 "current_value": 25000,
#             },
#             {
#                 "ticker": "BND",
#                 "name": "Vanguard Total Bond Market ETF",
#                 "asset_class": "Bond",
#                 "region": "US",
#                 "sector": "Bonds",
#                 "weight_percent": 30.0,
#                 "current_value": 15000,
#             },
#             {
#                 "ticker": "VXUS",
#                 "name": "Vanguard Total International Stock ETF",
#                 "asset_class": "Equity",
#                 "region": "International",
#                 "sector": "Broad Market",
#                 "weight_percent": 20.0,
#                 "current_value": 10000,
#             },
#         ],
#     }

# app = create_workflow()

# messages = app.invoke({
#     "messages": [HumanMessage(content="What is budgeting?")],
#     "next_agent": "",
#     "context": "portfolio",
#     "portfolio_json": sample_portfolio,
#     "user_goal": "Optimize for long-term growth."
# }, 
# {"configurable": {"thread_id": "1"}}
# )

# print(messages['messages'][-1])
# print(isinstance(messages['messages'][-1], BaseMessage))
# print(isinstance(messages['messages'][-1], PortfolioInsights))