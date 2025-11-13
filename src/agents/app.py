from model import GoalPlanResult, PortfolioInsights
import streamlit as st
# from agents import portfolio_insights
from data.portfolios import simple_portfolio
import json
from workflow import create_workflow
from langchain_core.messages import HumanMessage
import matplotlib.pyplot as plt
from qa_agent_test import get_response
from cachetools import cached, TTLCache
import datetime
import matplotlib.dates as mdates
import logging

st_logger = logging.getLogger('streamlit')
st_logger.setLevel(logging.INFO)

app = create_workflow()

# Initialize Streamlit state
if "messages" not in st.session_state:
    st.session_state.messages = []


def plot_price_history(history_data: dict, ticker: str = "Stock", show_volume: bool = False):
    """
    Creates a matplotlib chart from 6-month history data.
    
    Args:
        history_data: Dictionary containing Date, Close, Volume, etc. from yf_snapshot
        ticker: Stock ticker symbol for chart title
        show_volume: Whether to show volume subplot
    """
    # Extract data from the history dictionary
    dates = history_data.get('Date', [])
    closes = history_data.get('Close', [])
    volumes = history_data.get('Volume', [])
    opens = history_data.get('Open', [])
    highs = history_data.get('High', [])
    lows = history_data.get('Low', [])
    
    if not dates or not closes:
        print("Error: No date or close price data found")
        return
    
    # Convert dates to datetime objects if they're not already
    if dates:
        # dates = [d.date() if hasattr(d, 'date') else d for d in dates]
        dates = [datetime.datetime.strptime(d, "%Y-%m-%d") if isinstance(d, str) else d for d in dates]

    # Create the plot
    if show_volume and volumes:
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), height_ratios=[3, 1])
        
        # Price chart
        ax1.plot(dates, closes, linewidth=2, color='blue', label='Close Price')
        ax1.fill_between(dates, lows, highs, alpha=0.3, color='lightblue', label='Daily Range')
        ax1.set_title(f'{ticker} - 6 Month Price History', fontsize=16, fontweight='bold')
        ax1.set_ylabel('Price ($)', fontsize=12)
        ax1.grid(True, alpha=0.3)
        ax1.legend()
        
        # Volume chart
        ax2.bar(dates, volumes, alpha=0.7, color='orange')
        ax2.set_title('Trading Volume', fontsize=12)
        ax2.set_ylabel('Volume', fontsize=12)
        ax2.set_xlabel('Date', fontsize=12)
        ax2.grid(True, alpha=0.3)
        
        # Format x-axis dates for both subplots
        for ax in [ax1, ax2]:
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            ax.xaxis.set_major_locator(mdates.MonthLocator())
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)

        st.pyplot(fig)  
    else:
        # Single price chart
        fig, ax1 = plt.subplots(figsize=(12, 6))
        ax1.plot(dates, closes, linewidth=2, color='blue', label='Close Price')
        if highs and lows:
            ax1.fill_between(dates, lows, highs, alpha=0.3, color='lightblue', label='Daily Range')
        
        ax1.set_title(f'{ticker} - 6 Month Price History', fontsize=16, fontweight='bold')
        ax1.set_ylabel('Price ($)', fontsize=12)
        ax1.set_xlabel('Date', fontsize=12)
        ax1.grid(True, alpha=0.3)
        ax1.legend()
        
        # Format x-axis dates
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax1.xaxis.set_major_locator(mdates.MonthLocator())
        plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)
    
        st.pyplot(fig)  
    # plt.tight_layout()
    # plt.show()

def display_portfolio_insights(insights: PortfolioInsights):
    """
    Display the contents of a PortfolioInsights object using Streamlit components.
    
    Args:
        insights: The PortfolioInsights object containing the portfolio analysis
    """
    
    # Portfolio Summary
    st.markdown("### Portfolio Summary")
    st.info(insights.summary)
    
    # Risk Level with color coding
    st.markdown("### Risk Assessment")
    risk_colors = {
        "low": "🟢",
        "moderate": "🟡", 
        "high": "🔴",
        "unclear": "⚪"
    }
    risk_color = risk_colors.get(insights.risk_level, "⚪")
    st.write(f"**Overall Risk Level:** {risk_color} {insights.risk_level.title()}")
    
    # Allocation Overviews in tabs
    tab1, tab2, tab3 = st.tabs(["Asset Class", "Region", "Sector"])
    
    with tab1:
        st.markdown("#### Allocation by Asset Class")
        if insights.allocation_overview_asset_class:
            for item in insights.allocation_overview_asset_class:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"**{item.category}**")
                    if item.comment:
                        st.caption(item.comment)
                with col2:
                    st.metric("some-label", f"{item.weight_percent:.1f}%", label_visibility="hidden")
        else:
            st.write("No asset class data available")
    
    with tab2:
        st.markdown("#### Allocation by Region")
        if insights.allocation_overview_region:
            for item in insights.allocation_overview_region:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"**{item.category}**")
                    if item.comment:
                        st.caption(item.comment)
                with col2:
                    st.metric("some-label", f"{item.weight_percent:.1f}%", label_visibility="hidden")
        else:
            st.write("No regional data available")
    
    with tab3:
        st.markdown("#### Allocation by Sector")
        if insights.allocation_overview_sector:
            for item in insights.allocation_overview_sector:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"**{item.category}**")
                    if item.comment:
                        st.caption(item.comment)
                with col2:
                    st.metric("some-label", f"{item.weight_percent:.1f}%", label_visibility="hidden")
        else:
            st.write("No sector data available")
    
    # Concentration Flags
    if insights.concentration_flags:
        st.markdown("### ⚠️ Concentration Risks")
        for flag in insights.concentration_flags:
            concern_colors = {
                "low": "🟢",
                "moderate": "🟡", 
                "high": "🔴"
            }
            concern_color = concern_colors.get(flag.concern_level, "⚪")
            
            with st.expander(f"{concern_color} {flag.label} - {flag.concern_level.title()} Risk ({flag.weight_percent:.1f}%)"):
                st.write(flag.explanation)
    else:
        st.success("✅ No significant concentration risks identified")
    
    # Diversification & Gaps
    if insights.diversification_and_gaps:
        st.markdown("### 📊 Diversification Analysis")
        for gap in insights.diversification_and_gaps:
            with st.expander(f"📋 {gap.topic}"):
                st.write(gap.explanation)
                if gap.potential_impact:
                    st.caption(f"**Potential Impact:** {gap.potential_impact}")
    
    # Fees & Efficiency
    if insights.fees_and_efficiency:
        st.markdown("### 💰 Fees & Cost Efficiency")
        
        if insights.fees_and_efficiency.overall_fee_level and insights.fees_and_efficiency.overall_fee_level != "unknown":
            fee_colors = {
                "low": "🟢",
                "average": "🟡",
                "high": "🔴"
            }
            fee_color = fee_colors.get(insights.fees_and_efficiency.overall_fee_level, "⚪")
            st.write(f"**Overall Fee Level:** {fee_color} {insights.fees_and_efficiency.overall_fee_level.title()}")
        
        if insights.fees_and_efficiency.observations:
            st.markdown("**Observations:**")
            for obs in insights.fees_and_efficiency.observations:
                st.write(f"• {obs}")
    
    # Suitability vs Time Horizon
    if insights.suitability_vs_time_horizon:
        st.markdown("### ⏰ Suitability Assessment")
        
        suitability_colors = {
            "poor": "🔴",
            "mixed": "🟡",
            "reasonable": "🟢",
            "good": "🟢",
            "unclear": "⚪"
        }
        
        suitability_color = suitability_colors.get(insights.suitability_vs_time_horizon.qualitative_fit, "⚪")
        st.write(f"**Portfolio Fit:** {suitability_color} {insights.suitability_vs_time_horizon.qualitative_fit.title()}")
        
        col1, col2 = st.columns(2)
        with col1:
            if insights.suitability_vs_time_horizon.assumed_horizon_years:
                st.metric("Investment Horizon", f"{insights.suitability_vs_time_horizon.assumed_horizon_years} years")
        with col2:
            if insights.suitability_vs_time_horizon.assumed_risk_tolerance:
                st.metric("Risk Tolerance", insights.suitability_vs_time_horizon.assumed_risk_tolerance.title())
        
        st.write(insights.suitability_vs_time_horizon.explanation)
    
    # Questions & Next Steps
    if insights.questions_and_next_steps:
        st.markdown("### ❓ Questions & Next Steps")
        for i, question in enumerate(insights.questions_and_next_steps, 1):
            st.write(f"{i}. {question}")
    
    # Disclaimer
    if insights.disclaimer:
        with st.expander("📋 Important Disclaimer"):
            st.write(insights.disclaimer)

def display_analysis(analysis: PortfolioInsights):
    st.subheader("Portfolio Analysis Results")

    st.markdown("### Summary")
    st.write(analysis.summary)

    st.markdown("### Allocation Overview")
    st.write("**By Asset Class:**")
    for item in analysis.allocation_overview_asset_class:
        st.write(f"- {item.comment}")

    st.write("**By Region:**")
    for item in analysis.allocation_overview_region:
        st.write(f"- {item.comment}")

    st.write("**By Sector:**")
    for item in analysis.allocation_overview_sector:
        st.write(f"- {item.comment}")

    st.markdown("### Risk & Concentration")
    st.write(f"**Risk Level:** {analysis.risk_level}")
    if analysis.concentration_flags:
        st.write("**Concentration Flags:**")
        for flag in analysis.concentration_flags:
            st.write(f"- {flag.label} {flag.concern_level} {flag.explanation}")
    else:
        st.write("No significant concentration flags.")

    st.markdown("### Diversification & Gaps")
    for gap in analysis.diversification_and_gaps:
        st.write(f"- {gap.explanation}")

    if analysis.fees_and_efficiency and analysis.fees_and_efficiency.observations:
        st.write("**Fees & Efficiency Observations:**")
        for obs in analysis.fees_and_efficiency.observations:
            st.write(f"- {obs}")
    else:
        st.write("No fee observations available.")

    if analysis.suitability_vs_time_horizon:
        st.markdown("### Suitability vs Time Horizon")
        st.write(f"**Explanation:** {analysis.suitability_vs_time_horizon.explanation}")

    if analysis.questions_and_next_steps:
        st.markdown("### Questions & Possible Next Steps")
        for question in analysis.questions_and_next_steps:
            st.write(f"- {question}")

    if analysis.disclaimer:
        st.markdown("### Disclaimer")
        st.write(analysis.disclaimer)


def portfolio_pie_chart(portfolio):
    # Prepare data
    labels = [holding['ticker'] for holding in portfolio['holdings']]
    sizes = [holding['weight_percent'] for holding in portfolio['holdings']]

    # Create pie chart
    fig, ax = plt.subplots()
    ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140)
    ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.

    st.pyplot(fig)

def handle_market_trends():
    st.subheader("Market Trends for a Ticker")

    ticker = st.text_input("Enter a stock ticker symbol (e.g., AAPL, MSFT):")

    if st.button("Get Market Trends"):
        if ticker:
            with st.spinner(f"Fetching market trends for {ticker}...", show_time=True):
                # insights = market_trends.get_market_trends_for_ticker(ticker)
                messages = app.invoke({
                                "context": "market_trends",
                                "market_trends_ticker": ticker,
                            }, {"configurable": {"thread_id": "1"}})
                insights = messages['messages'][-1].content
                # print(messages['messages'][-1])
                current_state = app.get_state({"configurable": {"thread_id": "1"}})
                # print("current_state:", current_state.values['market_trends_agent_tools_out'])
                if 'market_trends_agent_tools_out' in current_state.values:
                    tool_outputs = current_state.values['market_trends_agent_tools_out']
                    print("tool_outputs:", tool_outputs)
                    print(type(tool_outputs))
                    # print(current_state['context'])
                    if "news" in tool_outputs:
                        st.markdown("### Recent News Articles")
                        for article in tool_outputs['news']:
                            title = article.get('title')
                            link = article.get('url', {}).get('url', '')
                            st.write(f"- [{title}]({link})")
                    else:
                        st.write("No recent news articles found.")

                    if "ticker_6mo_price_history" in tool_outputs:
                        st.markdown("### Price History Chart")
                        plot_price_history(tool_outputs['ticker_6mo_price_history'], ticker)

                st.markdown(f"### Market Trends for {ticker}: ")
                st.write(insights)  # Preserve line breaks in Streamlit
        else:
            st.error("Please enter a valid ticker symbol.")

def handle_portfolio_insights():
    st.subheader("Portfolio Insights")
    st.text("Example Portfolio JSON")
    st.json(simple_portfolio, expanded=False)

    uploaded_file = st.file_uploader("Choose a portfolio JSON file (Example above)", type=["json"])

    if uploaded_file is not None:
        try:
            portfolio = json.load(uploaded_file)
            st.write("JSON file uploaded successfully:")
            st.json(portfolio) # Use st.json to display as interactive JSON

            user_goal = st.text_input("Add an optional question/goal for your portfolio")
            if st.button("Analyze Portfolio"):
                with st.spinner("Analyzing portfolio...", show_time=True):
                    # analysis = portfolio_insights.analyze_portfolio(portfolio, user_goal)
                    messages = app.invoke({
                        "context": "portfolio",
                        "portfolio_json": portfolio,
                        "user_goal": user_goal,
                    }, {"configurable": {"thread_id": "1"}})
                    analysis = messages['messages'][-1]
                    print("portfolio:", messages['portfolio_json'])
                    portfolio_pie_chart(messages['portfolio_json'])
                    st.json(analysis, expanded=False)  # Display raw JSON output
                    # display_analysis(analysis)
                    display_portfolio_insights(analysis)
        except json.JSONDecodeError:
            st.error("Error decoding JSON. Please ensure the file is valid JSON.")


def handle_goal_planning_output(goalPlanResult: GoalPlanResult):
    """
    Display the contents of a GoalPlanResult object using Streamlit components.
    
    Args:
        goalPlanResult: The GoalPlanResult object containing the financial plan
    """
    
    # Natural Language Summary
    if goalPlanResult.natural_language_summary:
        st.markdown("### Plan Summary")
        st.info(goalPlanResult.natural_language_summary.replace("$", "\\$"))
    
    # User Profile
    st.markdown("### Your Profile")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Current Age", f"{goalPlanResult.user_profile.current_age} years")
        st.metric("Currency", goalPlanResult.user_profile.currency)
        st.metric("Risk Tolerance", goalPlanResult.user_profile.risk_tolerance.title())
    
    with col2:
        if goalPlanResult.user_profile.annual_income:
            st.metric("Annual Income", f"${goalPlanResult.user_profile.annual_income:,.0f}")
        if goalPlanResult.user_profile.monthly_expenses:
            st.metric("Monthly Expenses", f"${goalPlanResult.user_profile.monthly_expenses:,.0f}")
        if goalPlanResult.user_profile.current_investments:
            st.metric("Current Investments", f"${goalPlanResult.user_profile.current_investments:,.0f}")
    
    # Overall Assessment
    st.markdown("### Overall Assessment")
    st.write(goalPlanResult.overall_assessment.summary)
    
    if goalPlanResult.overall_assessment.overall_health_score is not None:
        # Create a progress bar for health score
        st.metric("Financial Health Score", f"{goalPlanResult.overall_assessment.overall_health_score:.0f}/100")
        st.progress(goalPlanResult.overall_assessment.overall_health_score / 100)
    
    # Key Strengths and Risks in columns
    col1, col2 = st.columns(2)
    
    with col1:
        if goalPlanResult.overall_assessment.key_strengths:
            st.markdown("**Key Strengths:**")
            for strength in goalPlanResult.overall_assessment.key_strengths:
                st.success(f"✓ {strength}")
    
    with col2:
        if goalPlanResult.overall_assessment.key_risks:
            st.markdown("**Key Risks:**")
            for risk in goalPlanResult.overall_assessment.key_risks:
                st.warning(f"⚠ {risk}")
    
    # Goals Section
    if goalPlanResult.goals:
        st.markdown("### Your Goals")
        
        for goal in goalPlanResult.goals:
            with st.expander(f"{goal.name} ({goal.type.replace('_', ' ').title()})"):
                
                # Goal metrics
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if goal.status:
                        status_color = {
                            "on_track": "🟢",
                            "slightly_behind": "🟡", 
                            "behind": "🔴",
                            "ahead": "🟢",
                            "unknown": "⚪"
                        }
                        st.write(f"**Status:** {status_color.get(goal.status, '⚪')} {goal.status.replace('_', ' ').title()}")
                    
                    if goal.priority:
                        st.write(f"**Priority:** {goal.priority.title()}")
                
                with col2:
                    if goal.time_horizon_years:
                        st.metric("Time Horizon", f"{goal.time_horizon_years:.1f} years")
                    if goal.target_age:
                        st.metric("Target Age", f"{goal.target_age:.0f} years")
                
                with col3:
                    if goal.target_amount_future:
                        st.metric("Target Amount", f"${goal.target_amount_future:,.0f}")
                    if goal.probability_of_success is not None:
                        st.metric("Success Probability", f"{goal.probability_of_success:.1%}")
                
                # Savings information
                if goal.required_monthly_savings or goal.current_monthly_savings:
                    st.markdown("**Savings Requirements:**")
                    savings_col1, savings_col2, savings_col3 = st.columns(3)
                    
                    with savings_col1:
                        if goal.required_monthly_savings:
                            st.metric("Required Monthly", f"${goal.required_monthly_savings:,.0f}")
                    
                    with savings_col2:
                        if goal.current_monthly_savings:
                            st.metric("Current Monthly", f"${goal.current_monthly_savings:,.0f}")
                    
                    with savings_col3:
                        if goal.gap_to_close is not None:
                            gap_color = "inverse" if goal.gap_to_close > 0 else "normal"
                            st.metric("Gap to Close", f"${goal.gap_to_close:,.0f}", delta_color=gap_color)
                
                # Action Recommendations
                if goal.action_recommendations:
                    st.markdown("**Recommended Actions:**")
                    for action in goal.action_recommendations:
                        priority_colors = {"high": "🔴", "medium": "🟡", "low": "🟢"}
                        st.write(f"{priority_colors.get(action.priority, '⚪')} **{action.priority.upper()}:** {action.recommendation}")
                        if action.estimated_impact:
                            st.caption(f"Expected impact: {action.estimated_impact}")
                
                # Goal-specific information
                if goal.goal_specific:
                    st.markdown("**Goal-Specific Details:**")
                    if goal.goal_specific.house_cost_future:
                        st.write(f"• House cost (future): ${goal.goal_specific.house_cost_future:,.0f}")
                    if goal.goal_specific.target_down_payment:
                        st.write(f"• Target down payment: ${goal.goal_specific.target_down_payment:,.0f}")
                    if goal.goal_specific.outstanding_balance:
                        st.write(f"• Outstanding balance: ${goal.goal_specific.outstanding_balance:,.0f}")
                    if goal.goal_specific.recommended_monthly_payment:
                        st.write(f"• Recommended monthly payment: ${goal.goal_specific.recommended_monthly_payment:,.0f}")
    
    # Scenario Analysis
    if goalPlanResult.scenario_analysis:
        st.markdown("### Scenario Analysis")
        
        for scenario in goalPlanResult.scenario_analysis:
            with st.expander(f"Scenario: {scenario.name}"):
                st.write(scenario.impact_summary)
                
                if scenario.changes:
                    st.markdown("**Changes in this scenario:**")
                    if scenario.changes.expected_return is not None:
                        st.write(f"• Expected return: {scenario.changes.expected_return:.1%}")
                    if scenario.changes.inflation_rate is not None:
                        st.write(f"• Inflation rate: {scenario.changes.inflation_rate:.1%}")
                    if scenario.changes.additional_monthly_savings is not None:
                        st.write(f"• Additional monthly savings: ${scenario.changes.additional_monthly_savings:,.0f}")
                    if scenario.changes.retirement_age_shift is not None:
                        st.write(f"• Retirement age shift: {scenario.changes.retirement_age_shift:+.0f} years")
                
                if scenario.suggested_adjustments:
                    st.markdown("**Suggested adjustments:**")
                    for adjustment in scenario.suggested_adjustments:
                        st.write(f"• {adjustment}")
    
    # Explanations and Disclaimers
    if goalPlanResult.explanations:
        with st.expander("📖 Explanations & Disclaimers"):
            
            if hasattr(goalPlanResult, "explanations") and hasattr(goalPlanResult.explanations, "key_terms") and goalPlanResult.explanations.key_terms:
                st.markdown("**Key Terms:**")
                for term, definition in goalPlanResult.explanations.key_terms.items():
                    st.write(f"**{term}:** {definition}")
            
            if hasattr(goalPlanResult, "explanations") and hasattr(goalPlanResult.explanations, "limitations") and goalPlanResult.explanations.limitations:
                st.markdown("**Limitations:**")
                for limitation in goalPlanResult.explanations.limitations:
                    st.write(f"• {limitation}")
            
            if hasattr(goalPlanResult, "explanations") and hasattr(goalPlanResult.explanations, "disclaimers") and goalPlanResult.explanations.disclaimers:
                st.markdown("**Disclaimers:**")
                for disclaimer in goalPlanResult.explanations.disclaimers:
                    st.write(f"• {disclaimer}")

def get_current_year():
    return datetime.datetime.now().year

def validate(goal_type, goal_target_amount, goal_target_year,
             current_net_worth, risk_tolerance, current_age,
             annual_income,  monthly_expenses, monthly_savings):
    return True, ""

def handle_goal_planning():
    st.subheader("Goal Planning")
    st.text("Define your financial goals and let the AI assist you in planning.")

    current_year = get_current_year()
    
    st.markdown("### Enter your financial goal below:")
    goal_input = st.radio("Select a goal type:", ("Retirement Planning", "Buying a Home", "Education Fund"))
    goal_target_amount = st.number_input("Target Amount ($):", min_value=0.0, step=10000.0, value=500000.0)
    goal_target_year = st.selectbox("Target year:", list(range(current_year + 1, current_year + 50)), index=10)

    st.markdown("### Enter your details:")
    current_net_worth = st.number_input("Current Net Worth ($):", min_value=0.0, step=10000.0, value=100000.0)
    risk_tolerance = st.selectbox("Risk Tolerance:", ["Low", "Moderate", "High"])
    current_age = st.number_input("Current Age:", min_value=18, max_value=100, value=30)
    annual_income = st.number_input("Annual Income ($):", min_value=0.0, step=10000.0, value=60000.0)
    monthly_expenses = st.number_input("Monthly Expenses ($):", min_value=0.0, step=500.0, value=2000.0)
    monthly_savings = st.number_input("Current Monthly Savings ($):", min_value=0.0, step=500.0, value=500.0)

    if st.button("Plan My Goal"):
        success, error_msg = validate(goal_input, goal_target_amount, 
                    goal_target_year, current_net_worth, risk_tolerance, 
                    current_age, annual_income, monthly_expenses, monthly_savings)
        if not success:
            st.error(f"Input validation error: {error_msg}")
        else:
            with st.spinner("Planning your financial goal...", show_time=True):
                messages = app.invoke(
                    {
                        "context": "goals_planning",
                        "goal_plan_inputs": {
                            "goal_type": goal_input,
                            "goal_target_amount": goal_target_amount,
                            "goal_target_horizon": goal_target_year - current_year,
                            "current_net_worth": current_net_worth,
                            "risk_tolerance": risk_tolerance,
                            "current_age": current_age,
                            "annual_income": annual_income,
                            "monthly_expenses": monthly_expenses,
                            "monthly_savings": monthly_savings
                        }
                    }, {"configurable": {"thread_id": "1"}})
                output = messages['goal_planning_output']
                print(output)
                st.markdown("### Your Financial Goal Plan:")
                handle_goal_planning_output(output)

def main():
    st.title("Finance AI Assistant")
    st.write("This is an AI assistant that can give insights on investment portfolios, do market trends analysis, and answer finance-related questions.")
    
    # Main interface
    tab1, tab2, tab3, tab4 = st.tabs(["Chat with Agent", "Portfolio Insights", "Market Trends", "Goal Planning"])

    with tab1:
        st.subheader("Chat with the Finance AI Assistant")
        st.write("Welcome to the Finance AI Assistant. How can I help you today?")

        prompt = st.chat_input("Ask a question about finance or investing...")

        # Initialize chat history
        if "messages" not in st.session_state:
            st.session_state.messages = []

        # Display chat messages from history on app rerun
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # React to user input
        if prompt:
            # Display user message in chat message container
            st.chat_message("user").markdown(prompt)
            # Add user message to chat history
            st.session_state.messages.append({"role": "user", "content": prompt})

            response = None
            with st.spinner("Getting response...", show_time=True):
                response = get_response(prompt)
            with st.chat_message("assistant"):
                st.markdown(response)
            # Add assistant response to chat history
            st.session_state.messages.append({"role": "assistant", "content": response})

    with tab2:
        handle_portfolio_insights()

    with tab3:
        handle_market_trends()

    with tab4:
        handle_goal_planning()

if __name__ == "__main__":
    main()