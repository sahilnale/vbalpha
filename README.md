# VB Alpha

## Overview

**VB Alpha** is a platform designed for stock enthusiasts and traders to monitor real-time stock data and create custom signals based on specific stock performance criteria. The platform also includes sentiment analysis features that provide insights into market sentiment surrounding particular stocks, helping users stay informed. A separate server handles the signals and sends notifications via email when predefined thresholds are met.

## Features

- **Real-time Stock Monitoring**: Keep track of your favorite stocks in real time.
- **Custom Signal Creation**: Set personalized signals for stock performance metrics, including price and volume changes.
- **Sentiment Analysis**: Gain insights into market sentiment through news articles related to your tracked stocks.
- **Email Notifications**: Receive timely email alerts when your stock signals are triggered. This feature is handled by a separate server to ensure performance and scalability.
- **User-friendly Interface**: A simple and intuitive interface for managing your stock signals and viewing analysis.

## How It Works

1. **Track Stocks**: Users can add stocks they want to track. The platform pulls real-time data to keep users updated on their stock performance.
2. **Set Custom Signals**: Users create signals based on stock metrics (e.g., if the stock price rises or falls beyond a certain value).
3. **Sentiment Analysis**: The platform analyzes market sentiment using news articles, offering users a broader view of how the stock is perceived.
4. **Email Notifications**: When a signal is triggered, the separate server running `signals.ipynb` sends an email notification to the user, keeping them informed without having to check the platform constantly.

### Structure

```bash
├── app.py                # Main Flask application
├── config.py             # Configuration for API keys, email settings, etc.
├── models.py             # Data models for stocks and signals
├── sentiment.py          # Sentiment analysis logic
├── Signals.ipynb # Jupyter notebook handling signals and sending emails (runs on a separate server)
├── requirements.txt      # Project dependencies
├── templates/            # HTML templates for the frontend
