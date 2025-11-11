from typing import TypedDict, Annotated, List, Optional
import operator
from langchain_core.messages import BaseMessage
from langchain_core.messages import ToolMessage, HumanMessage
from fin_tools import get_ticker_info, enhance_portfolio_data
from retrieval_tool import retrieve_documents
from qa_agent_test import get_qa_agent
from portfolio_insights import get_portfolio_insights_agent
import json
from model import PortfolioInsights
from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.memory import InMemorySaver

class AssistantState(TypedDict):
    """Simple state schema for multiagent system"""

    # Conversation history - persisted with checkpoint memory
    messages: Annotated[List[BaseMessage], operator.add]

    context: str

    portfolio_json: Optional[dict]

    # Agent routing
    next_agent: Optional[str]

    # Current user goal
    user_goal: Optional[str]


qa_agent = get_qa_agent()

portfolio_agent = get_portfolio_insights_agent()

# Agent node functions
def qa_agent_node(state: AssistantState):
    """Itinerary planning agent node"""
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


# Agent node functions
def portfolio_agent_node(state: AssistantState):
    """Portfolio analysis agent node"""
    print("Invoking portfolio agent...")
    print("portfolio_json:", state["portfolio_json"])
    print("user_goal:", state["user_goal"])
    response = portfolio_agent.invoke({
            "portfolio_json": state["portfolio_json"],
            "user_goal": state["user_goal"],
        })
    # print(response)
    return {"messages": [response]}

def portfolio_enhance_node(state: AssistantState):
    """Portfolio enhancement node"""
    print("Enhancing portfolio data...")
    portfolio_json = state["portfolio_json"]
    enhanced_portfolio_str = enhance_portfolio_data.invoke(json.dumps(portfolio_json, default=str))
    enhanced_portfolio = json.loads(enhanced_portfolio_str)
    print("enhanced_portfolio:", enhanced_portfolio)
    return {
        "portfolio_json": enhanced_portfolio
    }


def router_node(state: AssistantState):
    """Router node - determines which agent should handle the query"""
    context = state.get("context", "qa")
    print(f"Routing to {context} agent...")
    next_agent = "qa_agent"
    if context == "market_insights":
        next_agent = "market_insights_agent"
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
    elif next_agent == "market_insights_agent":
        return "market_insights_agent"
    elif next_agent == "goals_planning_agent":
        return "goals_planning_agent"
    else:
        # Default fallback
        return "qa_agent"

def create_workflow():
    checkpointer = InMemorySaver()

    workflow = StateGraph(AssistantState)

    workflow.add_node("router", router_node)
    workflow.add_node("portfolio_agent", portfolio_agent_node)
    workflow.add_node("portfolio_enhance", portfolio_enhance_node)
    workflow.add_node("qa_agent", qa_agent_node)

    workflow.set_entry_point("router")

    workflow.add_conditional_edges(
        "router",
        route_to_agent,
        {
            "qa_agent": "qa_agent",
            "portfolio_enhance": "portfolio_enhance",
            # "market_insights_agent": "market_insights_agent",
            # "goals_planning_agent": "goals_planning_agent"
        }
    )

    workflow.add_edge("portfolio_enhance", "portfolio_agent")
    workflow.add_edge("portfolio_enhance", END)
    workflow.add_edge("qa_agent", END)

    app = workflow.compile(checkpointer=checkpointer)
    return app


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