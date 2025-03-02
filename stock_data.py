import yfinance as yf

def get_stock_price(ticker):
    stock = yf.Ticker(ticker)
    price = stock.history(period="1d")["Close"].iloc[-1]
    return f"The latest price of {ticker.upper()} is ${price:.2f}"

# Example Usage
if __name__ == "__main__":
    ticker = input("Enter stock ticker: ")
    print(get_stock_price(ticker))
