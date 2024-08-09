from flask import Flask, render_template, redirect, url_for, flash, request
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from pymongo import MongoClient
from bson.objectid import ObjectId
import logging
import yfinance as yf
import smtplib
from email.mime.text import MIMEText
from email.message import EmailMessage
import pytz
import os
import ssl

from sentiment import sentiment

import time
from datetime import datetime, timedelta

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['MONGO_URI'] = "mongodb+srv://sahilnale:Logic!23@cluster0.y5amboq.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

@app.template_filter('currency')
def currency_format(value):
    return "{:,.2f}".format(value)

@app.template_filter('comma_format')
def comma_format(value):
    return "{:,}".format(value)

@app.template_filter('currency_format')
def currency_format(value):
    formatted_value = "{:,.2f}".format(abs(value))
    if value < 0:
        return f"-${formatted_value}"
    else:
        return f"${formatted_value}"

# MongoDB client setup
client = MongoClient(app.config['MONGO_URI'])
app.db = client.stocks  # Accessing the 'stocks' database

bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

logging.basicConfig(level=logging.DEBUG)

# Email configuration
EMAIL_USER = 'alerts4vbalpha@gmail.com'
EMAIL_PASS = 'yqhw llcy ttlv pdin'
EMAIL_SENDER = EMAIL_USER

@app.errorhandler(404)
def page_not_found(e):
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    else:
        return redirect(url_for('login'))

@login_manager.user_loader
def load_user(user_id):
    logging.debug(f"Loading user with ID: {user_id}")
    user = app.db.users.find_one({"_id": ObjectId(user_id)})
    if user:
        logging.debug(f"User found: {user}")
        return User(user['username'], user['email'], user['password'], user['_id'], user.get('stocks', []), user.get('signals', []))
    return None

def calculate_rsi(ticker, window=14):
    start_date = '2023-01-01'
    end_date = datetime.today().strftime('%Y-%m-%d')

    data = yf.download(ticker, start=start_date, end=end_date)

    if data.empty:
        return None
    delta = data['Close'].diff(1)
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=window).mean()
    avg_loss = loss.rolling(window=window).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return round(rsi[-1], 2)

def get_volume_surge(ticker, days):
    end_date = datetime.today()
    start_date = end_date - timedelta(days=days)
    data = yf.download(ticker, start=start_date.strftime('%Y-%m-%d'), end=end_date.strftime('%Y-%m-%d'))
    if data.empty:
        return None
    delta = data['Volume']
    avg_volume = delta.mean()
    curr_volume = delta.iloc[-1]
    return round(100 * (curr_volume - avg_volume) / avg_volume, 2)

class User(UserMixin):
    def __init__(self, username, email, password, id=None, stocks=None, signals=None):
        self.username = username
        self.email = email
        self.password = password
        self.id = str(id) if id else None
        self.stocks = stocks if stocks else []
        self.signals = signals if signals else []

    @staticmethod
    def from_mongo(data):
        return User(username=data['username'], email=data['email'], password=data['password'], id=data['_id'], stocks=data.get('stocks', []), signals=data.get('signals', []))

    @staticmethod
    def get_by_username(username):
        logging.debug(f"Fetching user with username: {username}")
        user = app.db.users.find_one({'username': username})
        if user:
            logging.debug(f"User found: {user}")
            return User.from_mongo(user)
        logging.debug("User not found")
        return None

    @staticmethod
    def get_by_id(user_id):
        logging.debug(f"Fetching user with ID: {user_id}")
        user = app.db.users.find_one({'_id': ObjectId(user_id)})
        if user:
            logging.debug(f"User found: {user}")
            return User.from_mongo(user)
        logging.debug("User not found")
        return None

    def save_to_db(self):
        logging.debug(f"Saving user: {self.username}")
        if self.id is None:
            # Create a new user document
            result = app.db.users.insert_one({
                'username': self.username,
                'email': self.email,
                'password': self.password,
                'stocks': self.stocks,
                'signals': self.signals
            })
            self.id = str(result.inserted_id)
        else:
            app.db.users.update_one(
                {'_id': ObjectId(self.id)},
                {'$set': {'username': self.username, 'email': self.email, 'password': self.password, 'stocks': self.stocks, 'signals': self.signals}},
                upsert=True
            )

    def add_stock(self, ticker):
        if any(stock['ticker'] == ticker for stock in self.stocks):
            flash(f'Stock {ticker} is already in your portfolio.', 'warning')
            return
        
        window = 14
        start_date = '2023-01-01'
        end_date = datetime.today().strftime('%Y-%m-%d')

        data = yf.download(ticker, start=start_date, end=end_date)

        stock = yf.Ticker(ticker)
        stock_name = stock.info['shortName']
        market_cap = stock.info['marketCap']
        eps = stock.info['trailingEps']
        pe_ratio = stock.info.get('trailingPE', '')
        shares_outstanding = stock.info['sharesOutstanding']
        ebitda = stock.info['ebitda']
        ps_ratio = stock.info['priceToSalesTrailing12Months']
        gross_margins = stock.info['grossMargins']
        operating_margins = stock.info['operatingMargins']
        ltm_revenue = stock.info['totalRevenue']
        ltm_fcf = stock.info['freeCashflow']
        enterprise_value = stock.info['enterpriseValue']
        sentiment_score = sentiment([ticker])
        volume_100 = get_volume_surge(ticker, 100)
        price = round(stock.history(interval="1m", period="1d")['Close'][-1], 2)
        rsi = calculate_rsi(ticker)
        stock_data = {'ticker': ticker, 'stock_name': stock_name, 'price': price, 'rsi': rsi, 'eps': eps, "Shares Outstanding": shares_outstanding, "ebitda": ebitda, "ps_ratio": ps_ratio, "pe_ratio": pe_ratio, "market_cap": market_cap, 'gross_margins': gross_margins, "operating_margins": operating_margins, "ltm_revenue": ltm_revenue, "ltm_fcf": ltm_fcf, 'sentiment': sentiment_score, 'volume_100': volume_100, 'enterprise_value': enterprise_value}
        self.stocks.append(stock_data)
        self.save_to_db()
        self.send_stock_added_email(stock_data)

    def add_signal(self, ticker, metric, percent_threshold):
        signal = {
            'ticker': ticker,
            'metric': metric,
            'percent_threshold': percent_threshold
        }
        self.signals.append(signal)
        self.save_to_db()
        flash('Signal has been added!', 'success')

    def update_stock_prices(self):
        for stock in self.stocks:
            stock_info = yf.Ticker(stock['ticker'])
            stock['price'] = round(stock_info.history(interval="1m", period="1d")['Close'][-1], 2)
        self.save_to_db()

    def send_stock_added_email(self, stock):
        subject = f"Stock Added: {stock['stock_name']}"
        body = f"Hello {self.username},\n\nYou have successfully added the stock {stock['stock_name']} (Ticker: {stock['ticker']}) with a price of ${stock['price']}.\n\nBest Regards,\nYour Stock Manager"
        em = EmailMessage()

        em['From'] = EMAIL_USER
        em['To'] = self.email
        em['Subject'] = subject
        em.set_content(body)

        context = ssl.create_default_context()

        try:
            with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
                smtp.login(EMAIL_USER, EMAIL_PASS)
                smtp.sendmail(EMAIL_SENDER, self.email, em.as_string())
                logging.debug(f"Email sent successfully for {stock['stock_name']}")
        except Exception as e:
            logging.error(f"Failed to send email for {stock['stock_name']}: {e}")

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        hashed_password = generate_password_hash(password)

        existing_user = User.get_by_username(username)
        if existing_user is None:
            new_user = User(username, email, hashed_password)
            new_user.save_to_db()
            flash('Your account has been created! You are now able to log in', 'success')
            email_sender = 'alerts4vbalpha@gmail.com'
            email_password = 'yqhw llcy ttlv pdin'
            email_receiver = 'sahilnalemail@gmail.com'
            subject = f'Thanks for registering'

            body = "You have registered to VB Alpha"
            em = EmailMessage()
            em['From'] = email_sender
            em['To'] = email_receiver
            em['Subject'] = subject
            em.set_content(body)

            context = ssl.create_default_context()

            with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
                smtp.login(email_sender, email_password)
                smtp.sendmail(email_sender, email_receiver, em.as_string())

            return redirect(url_for('login'))
        else:
            flash('Username already exists. Please choose a different one.', 'danger')

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.get_by_username(username)

        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Login Unsuccessful. Please check username and password', 'danger')

    return render_template('login.html')

@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    if request.method == 'POST':
        ticker = request.form['ticker']
        current_user.add_stock(ticker)
        flash('Stock has been added!', 'success')
        return redirect(url_for('dashboard'))
    
    current_user.update_stock_prices()  # Update stock prices on page load
    return render_template('dashboard.html', stocks=current_user.stocks, signals=current_user.signals)


@app.route('/add_signal', methods=['GET', 'POST'])
@login_required
def add_signal():
    if request.method == 'POST':
        ticker = request.form['ticker']
        metric = request.form['metric']
        threshold = request.form['percent_threshold']
        
        # Add the signal to the user's signals
        current_user.add_signal(ticker, metric, threshold)
        
        return redirect(url_for('dashboard'))
    
    return render_template('add_signal.html')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
