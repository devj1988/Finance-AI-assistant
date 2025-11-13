from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel
from typing import Any, Dict
from dotenv import load_dotenv
from langchain_core.output_parsers import StrOutputParser
from model import GoalPlanResult

load_dotenv()  # take environment variables from .env file

from prompts import goal_planning_system_prompt

llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.0)

llm_with_tools = llm.bind_tools([])
structured_llm = llm_with_tools.with_structured_output(GoalPlanResult)  # if using tools

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", goal_planning_system_prompt),
        (
            "user",
            """
            Here is the user's goal planning context.

            Goal Type: {goal_type}
            Target Amount (in $): {goal_target_amount}
            Target Horizon (years): {goal_target_horizon}
            Current Net Worth (in $): {current_net_worth}
            Risk Tolerance: {risk_tolerance}
            Current Age: {current_age}
            Annual Income (in $): {annual_income}
            Monthly Expenses (in $): {monthly_expenses}
            Monthly Savings (in $): {monthly_savings}

            Based on this information, provide personalized financial advice to help the user achieve their goal.
            """,
        ),
    ],
)

# agent = prompt | llm_with_tools | StrOutputParser()
agent = prompt | structured_llm

def get_goal_planning_agent():
    return agent

def get_goal_planning_advice(inputs: Dict[str, Any]) -> str:
    return agent.invoke(
        {
                "goal_type": inputs.get("goal_type"),
                "goal_target_amount": inputs.get("goal_target_amount"),
                "goal_target_horizon": inputs.get("goal_target_horizon"),
                "current_net_worth": inputs.get("current_net_worth"),
                "risk_tolerance": inputs.get("risk_tolerance"),
                "current_age": inputs.get("current_age"),
                "annual_income": inputs.get("annual_income"),
                "monthly_expenses": inputs.get("monthly_expenses"),
                "monthly_savings": inputs.get("monthly_savings"),
        }
    )


# Example usage
if __name__ == "__main__":
    goal_planning_input = {
        "goal_type": "Retirement",
        "goal_target_amount": 1000000,
        "goal_target_horizon": 20,
        "current_net_worth": 200000,
        "risk_tolerance": "Moderate",
        "current_age": 35,
        "annual_income": 80000,
        "monthly_expenses": 3000,
    }

    insights = get_goal_planning_advice(goal_planning_input)
    print("Goal Planning Advice:", insights)
    print(insights.model_dump_json(indent=2))  # or however you want to display the insights
