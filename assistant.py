from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
import torch
import yfinance as yf
import re
import random

# Load pre-trained FLAN-T5 model and tokenizer
model_name = "google/flan-t5-base"  # Using base instead of small for better results
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSeq2SeqLM.from_pretrained(model_name)

# Dictionary to store user-provided data
user_data = {}

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
        
        return {
            "success": True,
            "message": f"The latest price of {company_name} ({ticker.upper()}) is ${price:.2f}",
            "price": price,
            "name": company_name,
            "ticker": ticker.upper()
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

def ask_question(question, context=""):
    """
    Generate a response using FLAN-T5 based on user-provided financial context.
    """
    # Check if the question is asking for investment advice
    if is_investment_advice_question(question):
        # For stock-specific advice
        stock_pattern = re.compile(r'(buy|sell|invest in) ([A-Za-z]+)')
        ticker_match = stock_pattern.search(question.lower())
        
        if ticker_match:
            # This is about a specific stock
            return get_predefined_response("stock_advice") + "\n\nRemember that past performance is not indicative of future results, and all investments carry risk."
        else:
            # General investment advice
            return get_predefined_response("investment_advice") + "\n\nIt's important to do your own research or consult with a financial advisor before making investment decisions."
    
    # Check if the question is about stock prices
    stock_pattern = re.compile(r'(?:price|value|quote|stock) (?:of|for) ([A-Za-z]+)')
    ticker_match = stock_pattern.search(question.lower())
    
    # Also check for direct stock commands
    direct_stock_pattern = re.compile(r'get stock ([A-Za-z]+)')
    direct_match = direct_stock_pattern.search(question.lower())
    
    # If stock ticker detected, fetch real-time data
    if ticker_match or direct_match:
        ticker = (ticker_match.group(1) if ticker_match else direct_match.group(1)).upper()
        stock_data = get_stock_price(ticker)
        
        if stock_data["success"]:
            # Store the stock data for future reference
            user_data[f"stock_{ticker}"] = f"${stock_data['price']:.2f}"
            return stock_data["message"]
        else:
            return stock_data["message"]
    
    # Create a more structured prompt with clear instructions and examples
    full_prompt = f"""
Task: You are a helpful financial assistant. Based on the financial information below, provide a thoughtful, accurate, and helpful response to the user's question.

Financial Data:
{context}

Question: {question}

Important: 
1. Provide specific, practical advice based on the user's financial data
2. Do not make up information that is not in the data
3. If you cannot answer based on the available data, say so clearly
4. Never recommend specific stocks or investments
5. Emphasize long-term financial principles like diversification and risk management

Your response:
"""
    
    # Tokenize with appropriate settings
    inputs = tokenizer(full_prompt, return_tensors="pt", padding=True, truncation=True, max_length=512)
    
    # Generate with better parameters
    with torch.no_grad():
        output = model.generate(
            **inputs, 
            max_length=200,
            min_length=40,  # Set minimum length to avoid extremely short responses
            do_sample=True,  # Enable sampling for more diverse responses
            top_p=0.90,      # Nucleus sampling parameter
            top_k=50,        # Limit vocabulary to top k tokens
            temperature=0.7, # Control randomness (lower = more focused)
            repetition_penalty=1.2  # Penalize repetition
        )
    
    response = tokenizer.decode(output[0], skip_special_tokens=True)
    
    # Filter out problematic responses
    if len(response) < 30 or response == question or response.lower() in question.lower():
        # Fall back to predefined responses if the model gives a poor answer
        if "invest" in question.lower() or "stock" in question.lower():
            return get_predefined_response("investment_advice")
        elif "save" in question.lower() or "saving" in question.lower():
            return get_predefined_response("savings")
        else:
            return "Based on the information provided, I'd need more details to give you a helpful answer on this topic. Could you provide more specifics about your financial situation and goals?"
    
    return response

# Handle multi-line input for financial data
def process_set_command(command):
    parts = command[4:].split(":", 1)
    if len(parts) != 2:
        return False, "Invalid format! Use: set key: value"
    
    key, value = parts
    user_data[key.strip()] = value.strip()
    return True, f"✅ Saved: {key.strip()} = {value.strip()}"

# Chat loop
print("💰 AI Financial Assistant is ready! Type 'exit' to quit.")
print("- Set your financial data using 'set key: value'")
print("- Type 'show data' to see all your stored information")
print("- Get stock prices with 'get stock TICKER' or 'what's the price of TICKER'")
print("- Ask any financial question based on your data")

while True:
    user_input = input("\nYou: ")
    
    if user_input.lower() == "exit":
        print("👋 Goodbye!")
        break
    
    elif user_input.lower() == "show data":
        if not user_data:
            print("No financial data has been set yet.")
        else:
            print("\n📊 Your Financial Data:")
            for key, value in user_data.items():
                print(f"- {key}: {value}")
        continue
    
    elif user_input.lower().startswith("set "):
        success, message = process_set_command(user_input)
        print(message)
        continue
    
    # Generate context string in a more structured format
    context_string = "\n".join([f"- {k}: {v}" for k, v in user_data.items()])
    
    # Generate response
    response = ask_question(user_input, context=context_string)
    
    print("💬 Assistant:", response)