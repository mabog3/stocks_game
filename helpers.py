import os
import requests
import urllib.parse
import yfinance as yf
import yahoo_fin as fin
import pandas as pd
import numpy as np 
import json
import plotly
import plotly.graph_objects as go
from yahoo_fin import stock_info as si

from flask import redirect, render_template, request, session
from functools import wraps


def apology(message, code=400): #citation: Finance distribution code 
    """Render message as an apology to user."""
    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", top=code, bottom=escape(message)), code


def login_required(f): # citation: from Finance distribution code (CS50 staff)
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

def test(symbol):
    try: 
        #return(si.get_live_price(symbol))
        return si.get_quote_table(symbol)
    except: 
        return None
    
def graph(symbol):
    old = si.get_data(symbol)
    old['date'] = old.index
    fig = go.Figure(data=[go.Candlestick(x=old['date'],
                                         open=old['open'],
                                         high=old['high'],
                                         low=old['low'],
                                         close=old['close'])])
    #fig.show()
    
def historicalPlot(symbol):
    dat = si.get_data(symbol)
    dat['date'] = dat.index
    data=[go.Candlestick(x=dat['date'],
                         open=dat['open'],
                         high=dat['high'],
                         low=dat['low'],
                         close=dat['close'])]
    graphJSON = json.dumps(data, cls=plotly.utils.PlotlyJSONEncoder) #sends 
    return graphJSON

def histLookup(symbol): 
    try:
        api_key = os.environ.get("API_KEY")
        url = f"https://cloud.iexapis.com/stable/stock/{urllib.parse.quote_plus(symbol)}/chart/5y/?token={api_key}"
        print(url)
        response = requests.get(url)
        response.raise_for_status()
    except requests.RequestException:
        return None
    
    try:
        # quote = response.json().loads()
        #return quote
        return response
    except:
        return None
    



def lookup(symbol): #citation: Finance distribution code 
    """Look up quote for symbol."""
    # Contact API
    try:
        api_key = os.environ.get("API_KEY")
        url = f"https://cloud-sse.iexapis.com/stable/stock/{urllib.parse.quote_plus(symbol)}/quote?token={api_key}"
        response = requests.get(url)
        response.raise_for_status()
    except requests.RequestException:
        return None
    try:
        quote = response.json()
    except (KeyError, TypeError, ValueError):
        return None
    # Parse response
    try:
        return {
            "name": quote["companyName"],
            "price": float(quote["latestPrice"]),
            "symbol": quote["symbol"]
        }
    except (KeyError, TypeError, ValueError):
        return None


def usd(value): #citation: Finance distribution code 
    """Format value as USD."""
    return f"${value:,.2f}"
