from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from dotenv import load_dotenv
from retrieval_tool import retrieve_documents
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from fin_tools import get_ticker_info

import sys
sys.path.append('../')

load_dotenv()

llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.0)

tools = [retrieve_documents, get_ticker_info]
llm_with_tools = llm.bind_tools(tools)

prompt = ChatPromptTemplate.from_messages([
    ("system", """
    You are a helpful financial assistant. 
     Be concise and accurate. 
     Answer finance-related questions ONLY. 
     If you don't know the answer, just say you don't know.
     Do not make up answers.

    You have access to the following tools:
        - get_ticker_info: Fetches basic information about a stock ticker using yfinance.
            Use the tool when the user asks for stock information.
        - retrieve_documents: Fetches relevant documents about finance topics.
            Use this tool to look up information on various finance topics. 
         
    Use the ReACT (reason, then act) approach to decide when to use tools.

    If the user query requires using a tool, decide which tool to use and provide the necessary input.
    Else, answer the question directly based on your knowledge.

    If you don't have enough information to answer or your search results do not contain information about the query, answer DONTKNOW. 

    Steps:
    1. Analyze the user's question.
    2. If needed, use the appropriate tool by specifying the tool name and input.
      2.1 Use get_ticker_info for stock ticker information.
      2.2 Use retrieve_documents for general finance topics.
    3. If you used a tool, wait for the tool's output before proceeding.
    4. Use the tool output as context, to supplement your own knowledge about finance and investing to formulate your final answer.
    5. Provide a clear and concise answer to the user's question.
    6. CITE THE SOURCE used in the response. CITE THE FULL URL if available. 
    6. Answer DONTKNOW if you don't have enough information to answer. 

    """), MessagesPlaceholder(variable_name="messages")])

qa_agent = prompt | llm_with_tools

def get_qa_agent():
    return qa_agent

# print(qa_agent.invoke({"messages": [HumanMessage(content="What is the stock price of AAPL?")]}))
# print(qa_agent.invoke({"messages": [HumanMessage(content="What is DCA in investing?")]}))

# messages = [HumanMessage("What is the stock price of AAPL?")]

messages = [HumanMessage("What is DCA in investing?")]

messages = []

def get_answer(user_input: str) -> str:
    messages = [HumanMessage(content=user_input)]

    ai_msg = qa_agent.invoke(messages)
    print("AI message:", ai_msg)
    messages.append(ai_msg)

    if hasattr(ai_msg, 'tool_calls') and ai_msg.tool_calls:
    # Check the tool calls in the response
        print(ai_msg.tool_calls)
        tool_map = {
            "get_ticker_info": get_ticker_info,
            "retrieve_documents": retrieve_documents,
        }
        # Step 2: Execute tools and collect results
        for tool_call in ai_msg.tool_calls:
            # Execute the tool with the generated arguments
            tool_result = tool_map[tool_call['name']].invoke(tool_call)
            messages.append(tool_result)

    # Step 3: Pass results back to model for final response
        final_response = qa_agent.invoke(messages)
        messages.append(final_response)
        return final_response.content
    else:
        return ai_msg.content



def get_response(user_input: str, thread_id: int) -> str:
    config = {"configurable": {"thread_id": thread_id}}
    input_message = HumanMessage(content=user_input)
    result = agent.invoke({"messages": [input_message]})
    return result["messages"][-1].content


# print(get_answer("What is DCA in investing? What is the stock price of BMNR"))
# print(get_answer("What is the stock price of AVGOOOO?"))

# print(get_answer("What is personal finance?"))

# print(get_answer("What is budgeting? Retrieve relevant documents to support your answer."))


# print(get_response("What is the stock price of AAPL?", thread_id=1))