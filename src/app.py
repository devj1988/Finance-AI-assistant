import streamlit as st
from agents import portfolio_insights
from data.portfolios import simple_portfolio
import json
from agents.qa_agent_gemini import get_response

# Initialize Streamlit state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "recording_duration" not in st.session_state:
    st.session_state.recording_duration = 5
if "mode" not in st.session_state:
    st.session_state.mode = "customer_service"  # Default to customer service mode

def display_analysis(analysis):
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

def handle_portfolio_insights():
    st.subheader("Example Portfolio JSON")
    st.json(simple_portfolio, expanded=False)

    uploaded_file = st.file_uploader("Choose a portfolio JSON file (Example above)", type=["json"])

    if uploaded_file is not None:
        try:
            portfolio = json.load(uploaded_file)
            st.write("JSON file uploaded successfully:")
            st.json(portfolio) # Use st.json to display as interactive JSON

            user_goal = st.text_input("Add an optional question/goal for your portfolio")
            if st.button("Analyze Portfolio"):
                with st.spinner("Analyzing portfolio..."):
                    analysis = portfolio_insights.analyze_portfolio(portfolio, user_goal)
                    st.json(analysis, expanded=False)  # Display raw JSON output
                    display_analysis(analysis)
        except json.JSONDecodeError:
            st.error("Error decoding JSON. Please ensure the file is valid JSON.")

def main():
    st.title("Finance AI Assistant")
    st.write("This is an AI assistant that can give insights on investment portfolios, do market trends analysis, and answer finance-related questions.")
    
    # Main interface
    tab1, tab2, tab3 = st.tabs(["Main", "Portfolio Insights", "Market Trends"])

    with tab1:
        st.subheader("Chat with the Finance AI Assistant")
        st.write("Welcome to the Finance AI Assistant. How can I help you today?")

        prompt = st.chat_input("Ask a question about finace or investing...")

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

            # response = f"Echo: {prompt}"
            response= get_response(prompt, 1)
            # Display assistant response in chat message container
            with st.chat_message("assistant"):
                st.markdown(response)
            # Add assistant response to chat history
            st.session_state.messages.append({"role": "assistant", "content": response})

    with tab2:
        st.subheader("Portfolio Insights")
        handle_portfolio_insights()

    with tab3:
        st.subheader("Market Trends")
        # handle_market_trends()

if __name__ == "__main__":
    main()