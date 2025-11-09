
from langchain.agents import create_agent
from dotenv import load_dotenv
from langchain_core.messages import AIMessage
from langgraph.checkpoint.memory import InMemorySaver  
from core.fin_tools import get_ticker_info
from utils.constants import MODEL_NAME

load_dotenv()  # take environment variables from .env file

from langchain.agents import create_agent

agent = create_agent(
    model=MODEL_NAME,
    tools=[get_ticker_info],
    system_prompt="""
    You are a helpful financial assistant. Be concise and accurate. Answer finance-related questions ONLY. If you don't know the answer, just say you don't know. Do not make up answers.
    
    
    You have access to the following tool:
    - get_ticker_info: Fetches basic information about a stock ticker using yfinance.
        Use the tool when the user asks for stock information.
    """,
    checkpointer=InMemorySaver(),
)

# executor = AgentExecutor(agent=agent, tools=[], verbose=True)

def get_response(user_input: str) -> str:
    result = agent.invoke({"messages": [{"role": "user", "content": user_input}]}, {"configurable": {"thread_id": "1"}},  )
    last_msg = {'content': "No response from AI."}
    for msg in result['messages']:
        if isinstance(msg, AIMessage):
            last_msg = msg
    return last_msg.content