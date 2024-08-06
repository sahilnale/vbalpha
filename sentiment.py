import pandas as pd
import requests
from bs4 import BeautifulSoup
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import numpy as np


def sentiment(tickers):
    news = pd.DataFrame()

    for ticker in tickers:
        url = f'https://finviz.com/quote.ashx?t={ticker}&p=d'
        ret = requests.get(
            url,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36'},
        )

        html = BeautifulSoup(ret.content, "html.parser")

        try:
            df = pd.read_html(
                str(html),
                attrs={'class': 'fullview-news-outer'}
            )[0]
            df.columns = ['Date', 'Headline']  # Correctly indented
            df['Ticker'] = ticker  # Optionally, add the ticker as a column
            news = pd.concat([news, df], ignore_index=True)
        except ValueError:
            return 0

    dateNTime = df.Date.apply(lambda x: ','+x if len(x)<8 else x).str.split(r' |,', expand = True).replace("", None).ffill()
    df = pd.merge(df, dateNTime, right_index=True, left_index=True).drop('Date', axis=1).rename(columns={0:'Date', 1:'Time'})
    df = df[df["Headline"].str.contains("Loading.") == False].loc[:, ['Date', 'Time', 'Headline']]
    df["Ticker"] = ticker
    news = pd.concat([news, df], ignore_index = True)
    news.head()

    nltk.download('vader_lexicon')

    # New words and values
    new_words = {
        'crushes': 10,
        'Buy': 100,
        'Strong Buy': 150,
        'gains': 100,
        'beats': 50,
        'misses': -50,
        'trouble': -100,
        'falls': -100,
        'sell': -100,
        'downgrade': -100,
        'upgraded': 100,
        'outperforms': 50,
        'underperforms': -50,
        'surges': 100,
        'plummets': -100,
        'soars': 100,
        'tumbles': -100,
        'rises': 50,
        'declines': -50,
        'jumps': 100,
        'dips': -50,
        'steady': 0,
        'volatile': -50,
        'bullish': 100,
        'bearish': -100,
        'optimistic': 50,
        'pessimistic': -50,
        'profit': 100,
        'loss': -100,
        'increase': 50,
        'decrease': -50,
        'positive': 50,
        'negative': -50,
        'strong': 50,
        'weak': -50,
        'growth': 50,
        'decline': -50,
        'record': 100,
        'high': 50,
        'low': -50,
        'gain': 50,
        'drop': -50,
        'rise': 50,
        'fall': -50,
        'up': 50,
        'down': -50,
        'advance': 50,
        'retreat': -50,
        'plunge': -100,
        'skyrocket': 100,
        'rebound': 50,
        'slump': -100,
        'jump': 100,
        'crash': -100,
        'collapse': -100,
        'spike': 50,
        'dip': -50,
    }
    # Instantiate the sentiment intensity analyzer with the existing lexicon
    vader = SentimentIntensityAnalyzer()

    # Update the lexicon
    vader.lexicon.update(new_words)
    # Use these column names
    columns = ['Ticker', 'Date', 'Time', 'Headline']
    # Convert the list of lists into a DataFrame
    scored_news = df
    # Iterate through the headlines and get the polarity scores
    scores = [vader.polarity_scores(Headline) for Headline in scored_news.Headline.values]
    # Convert the list of dicts into a DataFrame
    scores_df = pd.DataFrame(scores)
    # Join the DataFrames
    scored_news = pd.concat([scored_news, scores_df], axis=1)


    scored_news.head()
    # prompt: Only store all value that have date todat in the scored_news
    scored_news = scored_news[scored_news['Date'] == 'Today']
    scored_news.head()


    return round(np.mean(scored_news['compound']),2)