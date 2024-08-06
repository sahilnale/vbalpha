import smtplib
from email.mime.text import MIMEText
from datetime import datetime
import pytz
import schedule
import time
import yfinance as yf

# Define classes for User, Stock, and Signal
class User:
    def __init__(self, name='', email=''):
        self.name = name
        self.email = email
        self.stocks = []
        self.signals = []

    def add_stock(self, stock):
        self.stocks.append(stock)

    def add_signal(self, signal):
        self.signals.append(signal)

class Stock:
    def __init__(self, ticker, name):
        self.ticker = ticker
        self.name = name
        self.price = self.get_initial_price()

    def get_initial_price(self):
        # Fetch the initial price using yfinance
        stock = yf.Ticker(self.ticker)
        return round(stock.history(interval="1m", period="1d")['Close'][-1], 2)

    def update_price(self):
        # Fetch the latest price using yfinance
        stock = yf.Ticker(self.ticker)
        self.price = round(stock.history(interval="1m", period="1d")['Close'][-1], 2)
        print(f'{self.name} (Ticker: {self.ticker}): New Price: ${self.price}')

class Signal:
    def __init__(self, stock, metric, lower_threshold, upper_threshold):
        self.stock = stock
        self.metric = metric
        self.lower_threshold = lower_threshold
        self.upper_threshold = upper_threshold
        self.lower_email_sent = False  # Flag to indicate if lower threshold email has been sent
        self.upper_email_sent = False  # Flag to indicate if upper threshold email has been sent

# Create a sample user with sample stocks and signals
user = User(name='Sahil Nale', email='sahilnalemail@gmail.com')

# Create sample stocks
stock1 = Stock(ticker='AAPL', name='Apple Inc.')
stock2 = Stock(ticker='GOOGL', name='Alphabet Inc.')

# Add stocks to user
user.add_stock(stock1)
user.add_stock(stock2)

# Create sample signals with lower and upper thresholds
signal1 = Signal(stock=stock1, metric='price', lower_threshold=140, upper_threshold=160)
signal2 = Signal(stock=stock2, metric='price', lower_threshold=2700, upper_threshold=2900)

# Add signals to user
user.add_signal(signal1)
user.add_signal(signal2)

# Email configuration
email_sender = 'alerts4vbalpha@gmail.com'
email_password = 'yqhw llcy ttlv pdin'
email_receiver = user.email

# Get the current time with timezone for the Bay Area (Pacific Time)
def get_current_time():
    timezone = pytz.timezone('America/Los_Angeles')
    return datetime.now(timezone).strftime('%H:%M %Z')

def send_email_for_stock(stock, threshold, condition):
    subject = f'Stock Update: {stock.name} at {get_current_time()}'
    body = f"Hello {user.name},\n\n"
    body += f"Stock: {stock.name} (Ticker: {stock.ticker}, Price: ${stock.price})\n"
    body += f"The price has {condition} the threshold of ${threshold}.\n"

    msg = MIMEText(body)
    msg['From'] = email_sender
    msg['To'] = email_receiver
    msg['Subject'] = subject

    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(email_sender, email_password)
            server.sendmail(email_sender, email_receiver, msg.as_string())
            print(f'Email sent successfully for {stock.name}')
    except Exception as e:
        print(f'Failed to send email for {stock.name}: {e}')

def check_thresholds():
    for signal in user.signals:
        if signal.metric == 'price':
            if signal.stock.price < signal.lower_threshold and not signal.lower_email_sent:
                send_email_for_stock(signal.stock, signal.lower_threshold, "fallen below")
                signal.lower_email_sent = True  # Mark lower threshold email as sent
            elif signal.stock.price >= signal.lower_threshold and signal.lower_email_sent:
                signal.lower_email_sent = False  # Reset the lower flag if the price rises above the threshold

            if signal.stock.price > signal.upper_threshold and not signal.upper_email_sent:
                send_email_for_stock(signal.stock, signal.upper_threshold, "risen above")
                signal.upper_email_sent = True  # Mark upper threshold email as sent
            elif signal.stock.price <= signal.upper_threshold and signal.upper_email_sent:
                signal.upper_email_sent = False  # Reset the upper flag if the price falls below the threshold

def update_prices():
    for stock in user.stocks:
        stock.update_price()
        check_thresholds()

# Schedule the task to update prices every minute
schedule.every(0.1).minutes.do(update_prices)

print("Scheduler started. Updating prices and checking thresholds every minute...")

# Keep the script running
while True:
    schedule.run_pending()
    time.sleep(0.1)
