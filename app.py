# app.py
import streamlit as st
import yfinance as yf
import pandas as pd
import re
import random
import plotly.graph_objects as go
import time
import numpy as np

st.set_page_config(
    page_title="AI Financial Assistant",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Apply custom CSS
st.markdown("""
<style>
    .main {
        padding: 1rem 1rem;
    }
    .assistant-message {
        background-color: #0a0a0a;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 0.5rem;
    }
    .user-message {
        background-color: #0a0a0a;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 0.5rem;
        text-align: right;
    }
    .title-container {
        display: flex;
        align-items: center;
        margin-bottom: 1rem;
    }
    .title-text {
        margin-left: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state variables if they don't exist
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Hello! I'm your AI Financial Assistant. How can I help you today?"}]

if "user_data" not in st.session_state:
    st.session_state.user_data = {}

# Pre-defined responses for common financial questions
FINANCIAL_RESPONSES = {
    "investment_advice": [
        "Based on your financial situation, I recommend considering a diversified portfolio that matches your risk tolerance and investment timeline. This might include a mix of stocks, bonds, and other assets.",
        "Investment decisions should be based on your financial goals, risk tolerance, and time horizon. Consider consulting with a financial advisor for personalized advice.",
        "When investing, it's important to diversify your portfolio across different asset classes and sectors to manage risk effectively."
    ],
    "stock_advice": [
        "Individual stock selections should be based on thorough research including the company's financials, growth prospects, competitive position, and overall market conditions.",
        "When considering individual stocks, look at factors like P/E ratio, earnings growth, debt levels, competitive advantages, and industry trends.",
        "Rather than focusing on individual stocks, many financial advisors recommend index funds for most investors as they provide diversification and typically have lower fees."
    ],
    "savings": [
        "A common financial guideline is to save 15-20% of your income for long-term goals like retirement, while maintaining an emergency fund of 3-6 months of expenses.",
        "Consider following the 50/30/20 rule: 50% of income for needs, 30% for wants, and 20% for savings and debt repayment.",
        "Building an emergency fund should be a priority before making significant investments in the market."
    ]
}

def get_stock_price(ticker):
    """
    Fetch the latest stock price using the yfinance library.
    """
    try:
        with st.spinner(f"Fetching data for {ticker}..."):
            stock = yf.Ticker(ticker)
            history = stock.history(period="1d")
            if history.empty:
                return {
                    "success": False,
                    "message": f"Could not find data for ticker symbol {ticker}."
                }
                
            price = history["Close"].iloc[-1]
            
            # Get additional information
            info = stock.info
            company_name = info.get('shortName', ticker.upper())
            
            # Get historical data for chart
            hist_data = stock.history(period="1y")
            
            return {
                "success": True,
                "message": f"The latest price of {company_name} ({ticker.upper()}) is ${price:.2f}",
                "price": price,
                "name": company_name,
                "ticker": ticker.upper(),
                "history": hist_data
            }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error fetching data for {ticker}: {str(e)}"
        }

def get_predefined_response(category):
    """Return a random predefined response from the specified category."""
    if category in FINANCIAL_RESPONSES:
        return random.choice(FINANCIAL_RESPONSES[category])
    return None

def is_investment_advice_question(question):
    """Check if the question is asking for investment advice."""
    investment_patterns = [
        r'(should|could|would) (i|me) (buy|sell|invest)',
        r'(is it|would it be) (worth|good|advisable) (to buy|to invest|investing)',
        r'(what|which) (stocks|investments|etfs|funds) (should|could|would) (i|me)',
        r'(recommend|suggestion|advice) (for|on) (investing|stocks|funds)'
    ]
    
    for pattern in investment_patterns:
        if re.search(pattern, question.lower()):
            return True
    return False

def extract_ticker_from_question(question):
    """Extract a potential stock ticker from a question."""
    # Check for stock prices
    stock_pattern = re.compile(r'(?:price|value|quote|stock) (?:of|for) ([A-Za-z]+)')
    ticker_match = stock_pattern.search(question.lower())
    
    # Check for direct stock commands
    direct_stock_pattern = re.compile(r'get stock ([A-Za-z]+)')
    direct_match = direct_stock_pattern.search(question.lower())
    
    # Check for buy/sell mentions
    trade_pattern = re.compile(r'(buy|sell|invest in) ([A-Za-z]+)')
    trade_match = trade_pattern.search(question.lower())
    
    if ticker_match:
        return ticker_match.group(1).upper()
    elif direct_match:
        return direct_match.group(1).upper()
    elif trade_match:
        return trade_match.group(2).upper()
    return None

def extract_loan_details(question):
    """Extract loan amount, interest rate, and term from a question."""
    # Extract loan amount
    amount_pattern = re.compile(r'(?:loan|borrow|debt) (?:of|for|worth) (?:\$|)(\d{1,3}(?:,\d{3})*|\d+)(?:\s|\.|,|k|K)')
    amount_match = amount_pattern.search(question)
    
    if not amount_match:
        amount_pattern = re.compile(r'(?:\$|)(\d{1,3}(?:,\d{3})*|\d+)(?:k|K|) (?:loan|debt)')
        amount_match = amount_pattern.search(question)
    
    # Extract interest rate
    rate_pattern = re.compile(r'(\d+(?:\.\d+)?)(?:\s|)%')
    rate_match = rate_pattern.search(question)
    
    # Extract term in years
    term_pattern = re.compile(r'(\d+)(?:\s|)(?:year|yr)')
    term_match = term_pattern.search(question)
    
    # Extract monthly payment inquiry
    payment_inquiry = "payment" in question.lower() or "pay" in question.lower() or "repay" in question.lower()
    
    # Process matches
    amount = None
    if amount_match:
        amount_str = amount_match.group(1).replace(',', '')
        if 'k' in question.lower() or 'K' in question:
            amount = float(amount_str) * 1000
        else:
            amount = float(amount_str)
    
    rate = rate_match.group(1) if rate_match else None
    term = term_match.group(1) if term_match else None
    
    return {
        "amount": amount,
        "rate": float(rate) if rate else None,
        "term": int(term) if term else None,
        "payment_inquiry": payment_inquiry
    }

def calculate_loan_payment(principal, annual_rate, years=None, months=None):
    """
    Calculate monthly payment for a loan.
    
    Parameters:
    principal (float): Loan amount
    annual_rate (float): Annual interest rate in percentage
    years (int, optional): Loan term in years
    months (int, optional): Loan term in months
    
    Returns:
    float: Monthly payment amount
    """
    if years is not None:
        months = years * 12
    elif months is None:
        # Default to 30 years if no term specified
        months = 30 * 12
    
    # Convert annual rate to monthly rate (and percentage to decimal)
    monthly_rate = annual_rate / 100 / 12
    
    # Calculate monthly payment using the loan formula
    monthly_payment = principal * (monthly_rate * (1 + monthly_rate) ** months) / ((1 + monthly_rate) ** months - 1)
    
    return monthly_payment

def calculate_investment_growth(principal, annual_rate, years, monthly_contribution=0):
    """
    Calculate investment growth with compound interest.
    """
    monthly_rate = annual_rate / 100 / 12
    total_months = years * 12
    
    # Formula for future value with regular contributions
    if monthly_contribution > 0:
        future_value = principal * (1 + monthly_rate) ** total_months + \
                        monthly_contribution * ((1 + monthly_rate) ** total_months - 1) / monthly_rate
    else:
        future_value = principal * (1 + monthly_rate) ** total_months
    
    return future_value

def handle_financial_question(question, user_data):
    """Handle various types of financial questions with calculations."""
    
    # Check for loan payment questions
    if any(word in question.lower() for word in ["loan", "borrow", "mortgage", "repay", "payment"]):
        loan_details = extract_loan_details(question)
        
        # If we found loan details and it looks like a payment question
        if loan_details["amount"] and loan_details["rate"] and loan_details["payment_inquiry"]:
            principal = loan_details["amount"]
            rate = loan_details["rate"]
            term_years = loan_details["term"] if loan_details["term"] else 30  # Default to 30 years
            
            # Calculate monthly payment
            monthly_payment = calculate_loan_payment(principal, rate, years=term_years)
            
            # Check if income is mentioned
            income_mentioned = "income" in question.lower() or "salary" in question.lower() or "earn" in question.lower()
            
            income = None
            # Look for income in user data or question
            if income_mentioned or any("income" in key.lower() for key in user_data.keys()):
                for key, value in user_data.items():
                    if "income" in key.lower() or "salary" in key.lower():
                        try:
                            # Extract number from value (e.g., "$5000 per month" -> 5000)
                            income_str = value.replace('$', '').replace(',', '')
                            # Check if it's annual or monthly
                            if "year" in value.lower() or "annual" in value.lower():
                                income = float(re.search(r'(\d+)', income_str).group(1)) / 12
                            else:
                                income = float(re.search(r'(\d+)', income_str).group(1))
                                
                            # If income seems very large, assume it's annual and convert to monthly
                            if income > 50000 and "month" not in value.lower():
                                income = income / 12
                                
                            break
                        except Exception as e:
                            print(f"Error parsing income: {e}")
                            pass
            
            # Create response with proper formatting
            response = f"For a {term_years}-year loan of ${principal:,.2f} at {rate}% interest rate:\n\n"
            response += f"• Monthly payment: ${monthly_payment:.2f}\n"
            response += f"• Total payment over {term_years} years: ${monthly_payment * term_years * 12:,.2f}\n"
            response += f"• Total interest paid: ${(monthly_payment * term_years * 12) - principal:,.2f}\n"
            
            if income:
                debt_ratio = (monthly_payment / income) * 100
                response += f"\nBased on your monthly income of ${income:,.2f}, "
                response += f"this loan payment would be {debt_ratio:.1f}% of your income. "
                
                if debt_ratio > 36:
                    response += "This is higher than the recommended 36% debt-to-income ratio, which may make it difficult to qualify for this loan."
                elif debt_ratio > 28:
                    response += "This is within the maximum recommended 36% debt-to-income ratio, but higher than the ideal 28% for housing expenses."
                else:
                    response += "This is below the recommended 28% of income for housing expenses, which is generally considered affordable."
            
            return response
    
    # Check for investment growth questions
    if any(word in question.lower() for word in ["invest", "return", "grow", "compound", "interest"]):
        # Look for amount, rate and term
        amount_pattern = re.compile(r'(?:\$|)(\d{1,3}(?:,\d{3})*|\d+)(?:k|K|)')
        amount_matches = amount_pattern.findall(question)
        
        rate_pattern = re.compile(r'(\d+(?:\.\d+)?)(?:\s|)%')
        rate_matches = rate_pattern.findall(question)
        
        year_pattern = re.compile(r'(\d+)(?:\s|)(?:year|yr)')
        year_matches = year_pattern.findall(question)
        
        # Check if we have enough information
        if amount_matches and rate_matches:
            principal = float(amount_matches[0].replace(',', ''))
            if 'k' in question.lower() or 'K' in question:
                principal *= 1000
                
            rate = float(rate_matches[0])
            years = int(year_matches[0]) if year_matches else 30  # Default to 30 years
            
            # Look for monthly contribution
            monthly_contribution = 0
            contribution_pattern = re.compile(r'contribute (?:\$|)(\d{1,3}(?:,\d{3})*|\d+)|(?:\$|)(\d{1,3}(?:,\d{3})*|\d+) (?:per|a|each) month')
            contribution_match = contribution_pattern.search(question)
            
            if contribution_match:
                group = contribution_match.group(1) if contribution_match.group(1) else contribution_match.group(2)
                monthly_contribution = float(group.replace(',', ''))
            
            # Calculate future value
            future_value = calculate_investment_growth(principal, rate, years, monthly_contribution)
            
            # Create response
            response = f"If you invest ${principal:,.2f}"
            if monthly_contribution > 0:
                response += f" with a monthly contribution of ${monthly_contribution:.2f}"
            response += f" at {rate}% annual return for {years} years:\n\n"
            response += f"• Future value: ${future_value:,.2f}\n"
            response += f"• Total growth: ${future_value - principal - (monthly_contribution * years * 12):,.2f}\n"
            
            if monthly_contribution > 0:
                total_contributions = monthly_contribution * years * 12
                response += f"• Total contributions: ${total_contributions:,.2f}\n"
                response += f"• Initial investment: ${principal:,.2f}\n"
            
            # Add a chart
            principal_amount = principal
            contribution_amount = 0
            growth_amount = 0
            
            data = []
            for year in range(years + 1):
                if year == 0:
                    data.append({
                        "Year": year,
                        "Principal": principal_amount,
                        "Contributions": contribution_amount,
                        "Growth": growth_amount,
                        "Total": principal_amount
                    })
                else:
                    # Calculate values for this year
                    total_start = data[year-1]["Total"]
                    contribution_year = monthly_contribution * 12
                    growth_year = (total_start + contribution_year/2) * (rate/100)  # Approximate growth with contributions
                    
                    # Update running totals
                    contribution_amount += contribution_year
                    growth_amount += growth_year
                    total = principal_amount + contribution_amount + growth_amount
                    
                    data.append({
                        "Year": year,
                        "Principal": principal_amount,
                        "Contributions": contribution_amount,
                        "Growth": growth_amount,
                        "Total": total
                    })
            
            # Create a DataFrame
            df = pd.DataFrame(data)
            
            # Create a Plotly figure
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=df["Year"],
                y=df["Principal"],
                name="Principal",
                marker_color='blue'
            ))
            
            if monthly_contribution > 0:
                fig.add_trace(go.Bar(
                    x=df["Year"],
                    y=df["Contributions"],
                    name="Contributions",
                    marker_color='green'
                ))
            
            fig.add_trace(go.Bar(
                x=df["Year"],
                y=df["Growth"],
                name="Growth",
                marker_color='orange'
            ))
            
            fig.update_layout(
                barmode='stack',
                title="Investment Growth Over Time",
                xaxis_title="Year",
                yaxis_title="Value ($)",
                legend_title="Components"
            )
            
            # Display the chart
            st.plotly_chart(fig, use_container_width=True)
            
            return response
    
    # Check for budgeting questions
    if any(word in question.lower() for word in ["budget", "save", "saving", "expense", "spend"]):
        if "50" in question and "30" in question and "20" in question:
            # User is asking about the 50/30/20 rule
            response = "The 50/30/20 budgeting rule suggests dividing your after-tax income as follows:\n\n"
            response += "• 50% for needs (housing, food, utilities, transportation, etc.)\n"
            response += "• 30% for wants (entertainment, dining out, hobbies, etc.)\n"
            response += "• 20% for savings and debt repayment\n\n"
            
            # Check if we have income information
            income = None
            for key, value in user_data.items():
                if "income" in key.lower() or "salary" in key.lower():
                    try:
                        income_match = re.search(r'(?:\$|)(\d{1,3}(?:,\d{3})*|\d+)', value)
                        if income_match:
                            income = float(income_match.group(1).replace(',', ''))
                            break
                    except:
                        pass
            
            if income:
                response += f"Based on your monthly income of ${income:,.2f}:\n\n"
                response += f"• Needs (50%): ${income * 0.5:,.2f}\n"
                response += f"• Wants (30%): ${income * 0.3:,.2f}\n"
                response += f"• Savings (20%): ${income * 0.2:,.2f}"
            
            return response
    
    # If no specific calculation matched, return None to use fallback responses
    return None
def handle_information_query(question, user_data):
    """Handle questions about stored user information with improved pattern recognition"""
    
    # More comprehensive check for income-related questions
    income_keywords = ["income", "salary", "earn", "make", "pay", "earning", "wage", "compensation"]
    question_words = ["what", "how much", "tell me", "show", "display", "reveal"]
    time_periods = ["month", "year", "annual", "monthly", "weekly", "hourly"]
    
    # Check if the question is asking about income/earnings
    is_income_question = any(word in question.lower() for word in income_keywords) and \
                        any(word in question.lower() for word in question_words)
    
    if is_income_question:
        # Look for income information in stored data
        income_data = None
        income_key = None
        
        for key, value in user_data.items():
            if any(word in key.lower() for word in income_keywords):
                income_data = value
                income_key = key
                break
        
        if income_data:
            # Determine if user wants monthly or annual income
            is_annual_request = any(period in question.lower() for period in ["year", "annual", "annually"])
            is_monthly_data = "month" in income_key.lower() or "month" in income_data.lower()
            
            try:
                # Extract the numeric value
                income_value = float(re.search(r'(\d[\d,]*\.?\d*)', income_data.replace('$', '')).group(1).replace(',', ''))
                
                # Convert between monthly and annual as needed
                if is_annual_request and is_monthly_data:
                    annual_value = income_value * 12
                    return f"Based on your monthly {income_key} of {income_data}, you earn ${annual_value:,.2f} per year."
                elif not is_annual_request and not is_monthly_data and "year" in income_data.lower():
                    monthly_value = income_value / 12
                    return f"Based on your annual {income_key} of {income_data}, you earn ${monthly_value:,.2f} per month."
                elif is_annual_request:
                    # If it's already annual data or unspecified
                    return f"Your annual {income_key} is {income_data}."
                else:
                    # If it's already monthly data or unspecified
                    return f"Your {income_key} is {income_data}."
            except:
                # If we can't parse the number, just return the raw data
                return f"Your {income_key} is {income_data}."
                
        return "I don't have any income information stored for you yet. You can set it using 'set monthly_income: $X' or through the Financial Data tab."
    
    # Check for other stored data queries (housing, savings, etc.)
    data_types = ["savings", "debt", "mortgage", "investment", "budget", "expense", "house", "home", "property"]
    for data_type in data_types:
        if data_type in question.lower() and any(word in question.lower() for word in question_words):
            for key, value in user_data.items():
                if data_type in key.lower():
                    return f"Your {key} is {value}."
            return f"I don't have any {data_type} information stored for you yet. You can set it using 'set {data_type}: $X' or through the Financial Data tab."
    
    return None

def ask_question(question, context=""):
    """
    Generate a response based on financial calculations and predefined responses.
    """
    # First, check if it's an information retrieval question
    info_response = handle_information_query(question, st.session_state.user_data)
    if info_response:
        return info_response
    # Check for ticker symbols in the question
    ticker = extract_ticker_from_question(question)
    
    # If we found a potential ticker symbol
    if ticker:
        # Check if it looks like a request for stock price
        if any(keyword in question.lower() for keyword in ["price", "value", "quote", "worth", "get stock"]):
            stock_data = get_stock_price(ticker)
            
            if stock_data["success"]:
                # Store the stock data for future reference
                st.session_state.user_data[f"stock_{ticker}"] = f"${stock_data['price']:.2f}"
                
                # Create a stock chart
                if "history" in stock_data:
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=stock_data["history"].index,
                        y=stock_data["history"]["Close"],
                        mode='lines',
                        name=f'{ticker} Price'
                    ))
                    fig.update_layout(
                        title=f"{stock_data['name']} ({ticker}) - 1 Year Performance",
                        xaxis_title="Date",
                        yaxis_title="Price ($)",
                        height=400
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                return stock_data["message"]
            else:
                return stock_data["message"]
    
    # Try to handle question with financial calculations
    calculated_response = handle_financial_question(question, st.session_state.user_data)
    if calculated_response:
        return calculated_response
    
    # Check if the question is asking for investment advice
    if is_investment_advice_question(question):
        # For stock-specific advice
        if ticker:
            # This is about a specific stock
            return get_predefined_response("stock_advice") + "\n\nRemember that past performance is not indicative of future results, and all investments carry risk."
        else:
            # General investment advice
            return get_predefined_response("investment_advice") + "\n\nIt's important to do your own research or consult with a financial advisor before making investment decisions."
    
    # For savings-related questions
    if any(word in question.lower() for word in ["save", "saving", "budget", "spend"]):
        return get_predefined_response("savings")
    
    # For questions we can't specifically answer
    return "I need more specific information to answer that question. Could you provide more details about your financial situation or clarify what you'd like to know?"

# App title and header
st.markdown('<div class="title-container"><h1>💰 AI Financial Assistant</h1></div>', unsafe_allow_html=True)

# Create tabs
tab1, tab2 = st.tabs(["Chat", "Your Financial Data"])

with tab1:
    # Display chat messages
    for message in st.session_state.messages:
        if message["role"] == "user":
            st.markdown(f'<div class="user-message">You: {message["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="assistant-message">💬 Assistant: {message["content"]}</div>', unsafe_allow_html=True)
    
    # Input for user message
    with st.form(key="chat_form", clear_on_submit=True):
        user_input = st.text_input("Ask a financial question:", key="user_input", placeholder="E.g., What's the price of AAPL?")
        submit_button = st.form_submit_button(label="Ask")
        
        # Process user input when form is submitted
        if submit_button and user_input.strip():
            # Check if it's a set command
            if user_input.lower().startswith("set "):
                try:
                    parts = user_input[4:].split(":", 1)
                    if len(parts) == 2:
                        key, value = parts
                    # If it's an income value, ensure it's properly formatted
                        if "income" in key.lower() or "salary" in key.lower():
                            # Clean the value and store it
                            st.session_state.user_data[key.strip()] = value.strip()
                            response = f"✅ Saved: {key.strip()} = {value.strip()}"
                        else:
                            st.session_state.user_data[key.strip()] = value.strip()
                            response = f"✅ Saved: {key.strip()} = {value.strip()}"
                    else:
                        response = "❌ Invalid format! Use: set key: value"
                except Exception as e:
                    response = f"❌ Error: {str(e)}"
            else:
                # Generate context string in a more structured format
                context_string = "\n".join([f"- {k}: {v}" for k, v in st.session_state.user_data.items()])
                
                # Add user message to chat history
                st.session_state.messages.append({"role": "user", "content": user_input})
                
                # Generate response
                with st.spinner("Thinking..."):
                    response = ask_question(user_input, context=context_string)
                
            # Add assistant response to chat history
            st.session_state.messages.append({"role": "assistant", "content": response})
            
            # Rerun to update the UI
            st.rerun()

with tab2:
    # Display user's financial data
    st.subheader("Your Stored Financial Information")
    
    if not st.session_state.user_data:
        st.info("You haven't added any financial data yet. Use 'set key: value' in the chat to add data.")
    else:
        # Create a dataframe from the user data
        data_df = pd.DataFrame(
            {"Category": list(st.session_state.user_data.keys()),
             "Value": list(st.session_state.user_data.values())}
        )
        st.table(data_df)
    
    # Add new data form
    with st.expander("Add New Data"):
        with st.form(key="add_data_form"):
            col1, col2 = st.columns(2)
            with col1:
                new_key = st.text_input("Category", placeholder="E.g., income, savings, debt")
            with col2:
                new_value = st.text_input("Value", placeholder="E.g., $5000 per month")
            
            add_button = st.form_submit_button("Add Data")
            if add_button and new_key and new_value:
                st.session_state.user_data[new_key] = new_value
                st.success(f"Added: {new_key} = {new_value}")
                time.sleep(1)
                st.rerun()
    
    # Clear all data button
    if st.button("Clear All Data") and st.session_state.user_data:
        st.session_state.user_data = {}
        st.success("All financial data cleared!")
        time.sleep(1)
        st.rerun()

# Display helpful information in the sidebar
with st.sidebar:
    st.subheader("How to Use This App")
    st.markdown("""
    **💬 Ask Financial Questions:**
    - Get stock prices: "What's the price of AAPL?"
    - Loan calculations: "How much will I pay for a $250,000 loan at 4.5% for 30 years?"
    - Investment growth: "How much will $10,000 grow at 7% for 20 years?"
    - Budgeting help: "How can I apply the 50/30/20 rule with my income?"
    
    **📊 Store Your Financial Data:**
    - Use "set category: value" in chat
    - Example: "set monthly_income: $5000"
    - Or use the form in the "Your Financial Data" tab
    
    **🔍 Get Stock Information:**
    - Ask about specific stocks to see price charts
    - Example: "Show me TSLA stock"
    """)
    
    st.subheader("Sample Questions")
    sample_questions = [
        "What's the price of AAPL?",
        "How much will I pay for a $250,000 loan at 4.5% for 30 years?",
        "If I invest $10,000 at 7% return for 20 years, how much will I have?",
        "How should I budget with my income using the 50/30/20 rule?",
        "If I contribute $500 per month to my investment of $5000 at 8% for 25 years, what will be the result?"
    ]
    for q in sample_questions:
        if st.button(q):
            # Add the question to messages and generate response
            st.session_state.messages.append({"role": "user", "content": q})
            
            # Generate context string
            context_string = "\n".join([f"- {k}: {v}" for k, v in st.session_state.user_data.items()])
            
            # Generate response
            response = ask_question(q, context=context_string)
            
            # Add assistant response to chat history
            st.session_state.messages.append({"role": "assistant", "content": response})
            
            # Rerun to update the UI
            st.rerun()