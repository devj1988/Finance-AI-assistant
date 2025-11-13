from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel
from typing import Any, Dict
from fin_tools import enhance_portfolio_data
from dotenv import load_dotenv
from model import PortfolioInsights  # or inline them
from prompts import portfolio_prompt

load_dotenv()  # take environment variables from .env file

llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.0)

llm_with_tools = llm.bind_tools([enhance_portfolio_data])
structured_llm = llm_with_tools.with_structured_output(PortfolioInsights)  # if using tools

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", portfolio_prompt),
        (
            "user",
            """Here is the user's portfolio and context as JSON:

            {portfolio_json}

            Within this portfolio, is a list of holdings, each with a ticker symbol.
            Use the enhance_portfolio_data tool to enhance the portfolio.

            User question or goal (if any):
            {user_goal}

            Analyze this portfolio and return ONLY valid JSON that matches the PortfolioInsights schema.
            Also, answer the user question or goal in the Summary section.


            """,
        ),
    ],
)

agent = prompt | structured_llm

def get_portfolio_insights_agent():
    return agent

def analyze_portfolio(portfolio: Dict[str, Any], user_goal: str = "") -> PortfolioInsights:
    """
    portfolio: your portfolio dict (same shape you’re sending to the LLM)
    user_goal: e.g. "Retire in ~20 years, moderate risk tolerance."
    """
    return agent.invoke(
        {
            "portfolio_json": portfolio,
            "user_goal": user_goal,
        }
    )


# Example usage
if __name__ == "__main__":
    sample_portfolio = {
        "base_currency": "USD",
        "holdings": [
            {
                "ticker": "VTI",
                "current_value": 25000,
            },
            {
                "ticker": "BND",
                "current_value": 15000,
            },
            {
                "ticker": "VXUS",
                "current_value": 10000,
            },
        ],
    }

    insights = analyze_portfolio(sample_portfolio, "Retire in ~20 years, moderate risk.")
    print(insights.model_dump_json(indent=2))  # or however you want to display the insights
