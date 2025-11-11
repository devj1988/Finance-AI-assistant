from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from dotenv import load_dotenv
from utils.constants import MODEL_NAME
from rag.vector_store import retrieve_documents
from langchain_core.prompts import ChatPromptTemplate
from core.fin_tools import get_ticker_info

load_dotenv()

llm = ChatGoogleGenerativeAI(model=MODEL_NAME, temperature=0.0)

tools = [retrieve_documents, get_ticker_info]
llm_with_tools = llm.bind_tools(tools)

prompt = ChatPromptTemplate.from_messages([
    ("system", """
    You are a helpful financial assistant. 
     Be concise and accurate. 
     Answer finance-related questions ONLY. 
     If you don't know the answer, just say you don't know.
     Do not make up answers.
    
    
    You have access to the following tool:
    - get_ticker_info: Fetches basic information about a stock ticker using yfinance.
        Use the tool when the user asks for stock information.
    - retrieve_documents: Fetches relevant documents about finance topics.
        Use this tool to look up information on various finance topics. 
    """)])

agent = prompt | llm_with_tools

from typing import List, Union
from langgraph.graph import StateGraph, MessagesState, START, END

# Define the graph state
class AgentState(MessagesState):
    # You can add other state variables here if needed
    pass

def call_model(state: AgentState):
    messages = state["messages"]
    response = agent.invoke(messages)
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