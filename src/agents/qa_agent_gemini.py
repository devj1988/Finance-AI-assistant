from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from dotenv import load_dotenv

load_dotenv()

llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.0)
tools = []
llm_with_tools = llm.bind_tools(tools)

from typing import List, Union
from langgraph.graph import StateGraph, MessagesState, START, END

# Define the graph state
class AgentState(MessagesState):
    # You can add other state variables here if needed
    pass

def call_model(state: AgentState):
    messages = state["messages"]
    response = llm.invoke(messages)
    # Return the updated state with the new AI message appended
    return {"messages": [response]}

from langgraph.checkpoint.memory import InMemorySaver
checkpointer = InMemorySaver()

workflow = StateGraph(AgentState)
workflow.add_node("agent", call_model)
workflow.add_edge("agent", END) # Simple graph, transitions to END after model call
workflow.add_edge(START, "agent")

app = workflow.compile(checkpointer=checkpointer)

# import uuid
# from langchain_core.runnables.config import RunnableConfig

# Generate a unique thread ID for the conversation
# thread_id = str(uuid.uuid4())
# config = {"configurable": {"thread_id": thread_id}}

# # First invocation
# input_message = HumanMessage(content="Hi! My name is Alex.")
# result1 = app.invoke({"messages": [input_message]}, config)
# print(result1["messages"][-1].content)

# # Second invocation using the same thread ID (memory is preserved)
# input_message2 = HumanMessage(content="What is my name?")
# result2 = app.invoke({"messages": [input_message2]}, config)
# print(result2["messages"][-1].content)
# print("Chat session ended.")


def get_response(user_input: str, thread_id: int) -> str:
    config = {"configurable": {"thread_id": thread_id}}
    input_message = HumanMessage(content=user_input)
    result = app.invoke({"messages": [input_message]}, config)
    return result["messages"][-1].content