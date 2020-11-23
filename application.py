import os

from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
import sys

from helpers import apology, login_required, lookup, usd




#TO DO: -learn to use ajax so page isnt reloaded every time something happens (and also JS)
#put game choice in layout, and see if I can render layout, so it's not copy-pasted everywhere




API_KEY = 'pk_0bae86416ffe40dea6604c256084d52d'
# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///finance.db'
db = SQLAlchemy(app)

@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    """Show portfolio of stocks"""
    # get user cash total
    if request.form.get("gamechoice"):
        session['game'] = int(request.form.get("gamechoice"))

    #NEED TO FIX: use ajax to stop every page from constant reload
    game = session['game']
    if game != 0:
        name = db.engine.execute("SELECT name FROM game WHERE gamenumber=?", game).fetchall()[0]['name']
        startingcash=round(db.engine.execute("SELECT * FROM game WHERE gamenumber=?", game).fetchall()[0]['starting_cash'])
    else:
        name = ""
        startingcash=10000

    portfolio = db.engine.execute("SELECT stock, quantity, price FROM portfolio WHERE user_id=? AND game=?", session["user_id"], game).fetchall()
    if not portfolio:  # load in cash
        db.engine.execute("INSERT INTO portfolio (user_id, stock, quantity, price, game) VALUES (:user_id,:stock,:startingcash, :dollar, :game)", user_id=session["user_id"], stock="Cash", startingcash=startingcash, dollar=1, game=game)
        portfolio = db.engine.execute("SELECT stock, quantity, price FROM portfolio WHERE user_id=? AND game=?", session["user_id"], game).fetchall()

    cash = round(db.engine.execute("SELECT * FROM portfolio WHERE stock=:cash AND user_id=:user_id AND game=:game", cash="Cash",user_id=session["user_id"], game=game).fetchall()[0]['quantity'], 2)
    grand_total = cash

    # determine current price, stock total value and grand total value
    stockDictList = []

    for stocks in portfolio:
        stock = dict(stocks)
        if stock['stock'] == "Cash":
            price = 1
            stock['quantity'] = cash
            total = cash
            stock.update({'price': price, 'total': total, 'quantity': cash})
            stockDictList.append(stock)
        else:
            quantity = round(stock['quantity'], 2)
            if quantity > 0.1: #in case of float errors
                price = lookup(stock['stock'])['price']
                total = stock['quantity'] * price
                stock.update({'price': price, 'total': total, 'quantity': quantity})
                grand_total += total
                stockDictList.append(stock)

    return render_template("index.html", games=db.engine.execute("SELECT * FROM game WHERE player1 IN (:user_id) OR player2 IN (:user_id)", user_id=session['user_id']), name=name, stocks=stockDictList, cash=cash, total=grand_total, game=game) #need to implement game choice

@app.route("/actionpage", methods=["GET", "POST"])
@login_required
def actionpage():
    """Get stock quote."""
    if request.method == "POST":
        # ensure name of stock was submitted
        if request.form.get("gamechoice"):
            session['game'] = int(request.form.get("gamechoice"))
        game = session['game']

        if game != 0:
            name = db.engine.execute("SELECT name FROM game WHERE gamenumber=?", game).fetchall()[0]['name']
        else:
            name = ""
        if request.form.get("buysymbol") and request.form.get("buyshares"):
            buyList = buy(request.form.get("buysymbol"), request.form.get("buyshares"), game)
            if buyList:
                flash('success')
        if request.form.get("sellsymbol") and request.form.get("sellshares"):
            sellList = sell(request.form.get("sellsymbol"), request.form.get("sellshares"), game)
            if sellList:
                flash('success')
        if request.form.get("cashInput"):
            c = round(float(request.form.get("cashInput")), 2)
            if c <= 0:
                flash('Cash quantity must be a positive real number')
                return render_template("addcash.html")
            # update cash amount in users database
            check = db.engine.execute("UPDATE portfolio SET quantity=quantity+:amt WHERE user_id=:user_id AND stock=:stock AND game=0", amt=c, user_id=session["user_id"], stock="Cash")
            if check:
                flash('Success')
                return render_template("addcash.html")
        return render_template("actionpage.html", stocks = db.engine.execute("SELECT * FROM portfolio WHERE user_id = :user_id AND quantity > 0", user_id=session["user_id"]),games=db.engine.execute("SELECT * FROM game WHERE player1 IN (:user_id) OR player2 IN (:user_id)", user_id=session['user_id']),name=name)

    # else if user reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("actionpage.html", stocks = db.engine.execute("SELECT * FROM portfolio WHERE user_id = :user_id AND quantity > 0", user_id=session["user_id"]), games=db.engine.execute("SELECT * FROM game WHERE player1 IN (:user_id) OR player2 IN (:user_id)", user_id=session['user_id']))

@app.route("/gamescreen", methods=["GET", "POST"])
@login_required
def gamescreen():
    currentgames = db.engine.execute("SELECT * FROM game WHERE (player1 IN (:user_id) OR player2 IN (:user_id)) AND initialized=1", user_id=session['user_id'])
    uname=str(db.engine.execute("SELECT * FROM users WHERE id=:user_id", user_id=session['user_id']).fetchall()[0]['username'])
    if request.method == "POST":
        return render_template("gamescreen.html", currentgames=currentgames)

    # else if user reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("gamescreen.html", currentgames=currentgames)

@app.route("/newgame", methods=["GET", "POST"])
@login_required
def newgame():
    if request.method == "POST":
        # ensure name of stock was submitted
        if not (request.form.get("player2")) and (request.form.get("gamename") and (request.form.get("days") or request.form.get("years") or request.form.get("months")))):
            flash('Please input a game name, duration, and second player')
            return render_template("newgame.html")
        startingcash = request.form.get("startingcash")
        if not startingcash:
            startingcash = 0
        player2uname = request.form.get("player2")
        gamename = request.form.get("gamename")
        rows = db.engine.execute("SELECT * FROM users WHERE username = ?", request.form.get("player2")).fetchall()
        if len(rows) < 1:
            flash("invalid username")
            return render_template("newgame.html")
        player2=db.engine.execute("SELECT * FROM users WHERE username=?",player2uname).fetchall()[0]['id']

        db.engine.execute("INSERT INTO game (player1, player2, name, initialized, starting_cash) VALUES (:player1, :player2, :name, :initialized, :startingcash)",
                  player1=session["user_id"], player2=player2, initialized=1, name=gamename, startingcash=startingcash)


        # stock name is valid
        return render_template("newgame.html")

    # else if user reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("newgame.html")


def buy(symbol, shares, game):
    if not (symbol and shares):
        flash("Please input a valid stock symbol and share quantity.")
        return []
    # ensure number of shares is valid
    # if not str.isdecimal(shares):
    #     flash('Share quantity must be a positive integer')
    #     return []
    if float(shares) <= 0:
        flash('Share quantity must be a positive real number.')
        return []
    # pull quote
    quote = lookup(symbol)

    # check is valid stock name provided
    if quote == None:
        flash('Please input a valid stock symbol.')
        return []
    # calculate cost of transaction
    cost = round(float(shares) * float(quote['price']), 2)

    # check if user has enough cash for transaction
    cashOnHand = db.engine.execute("SELECT * FROM portfolio WHERE stock=:cash AND user_id=:user_id AND game=:game", cash="Cash", user_id=session["user_id"], game=game).fetchall()
    if cost > cashOnHand[0]["quantity"]:
        flash('Insufficient Funds')
        return []
    # update cash amount in users database
    db.engine.execute("UPDATE PORTFOLIO SET quantity=quantity-:cost WHERE user_id=:user_id AND game=:game AND stock=:cash", cost=cost, game=game, user_id=session["user_id"], cash="Cash")
    # y = db.engine.execute("SELECT cash FROM users WHERE id = ?", session["user_id"]).fetchall()
    # c = round(y[0]['cash'], 2)

    # add transaction to transaction db for history
    db.engine.execute("INSERT INTO transactions (user_id, stock, quantity, price, date, type, total, game) VALUES (:user_id, :stock, :quantity, :price, :date, :type1, :total, :game)",
                                 user_id=session["user_id"], stock=quote["symbol"], type1='BOUGHT', total=cost, quantity=float(shares), price=quote['price'], date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), game=game)

    # check if stock already owned for db organization
    rows = db.engine.execute("SELECT quantity FROM portfolio WHERE stock=:stock AND user_id=:user_id AND game=:game", stock=quote["symbol"], user_id=session['user_id'], game=game).fetchall()
    if not rows:
        db.engine.execute("INSERT INTO portfolio (user_id, stock, quantity, game) VALUES (:user_id, :stock, :quantity, :game)",
                   stock=quote["symbol"], quantity=float(shares), user_id=session["user_id"], game=game)

    # if symbol is already in portfolio, update share quantity
    else:
        db.engine.execute("UPDATE portfolio SET quantity=quantity+:quantity WHERE stock=:stock AND user_id=:user_id AND game=:game",
                   quantity=float(shares), stock=quote["symbol"], user_id=session['user_id'], game=game)

    if float(shares) == 1:
        words = ["share", "was"]
    else:
        words = ["shares", "were"]
    return [words, round(quote['price'], 2), cost]

def sell(symbol, shares, game):
    """Sell shares of stock"""
        # ensure stock symbol and number of shares was submitted
    if not symbol and shares:
        flash("Please input a valid stock symbol and share quantity.")
        return []
    # ensure number of shares is valid
    if float(shares) <= 0:
        flash('Share quantity must be a positive real number.')
        return []
    # pull quote
    quote = lookup(symbol)

    # check is valid stock name provided
    if quote == None:
        flash('Please input a valid stock symbol.')
        return []
    # check if user has enough of the stock to sell
    rows = db.engine.execute("SELECT quantity FROM portfolio WHERE stock=:stock AND user_id=:user_id AND game=:game", stock=quote["symbol"], user_id=session['user_id'], game=game).fetchall()
    if not rows:
        flash('You do not currently own this stock.')
        return []

    # check if enough of the stock in the portfolio
    if rows[0]["quantity"] < float(shares):
        flash('You do not have enough shares of this stock.')
        return []

    # calculate price of transaction
    price1 = round(float(shares) * float(quote['price']), 2)

    db.engine.execute("UPDATE portfolio SET quantity=quantity-:quantity WHERE stock=:stock AND user_id=:user_id AND game=:game",
               quantity=round(float(shares), 2), stock=quote["symbol"], user_id=session['user_id'], game=game)
    db.engine.execute("UPDATE portfolio SET quantity=quantity+:price WHERE user_id=:user_id AND stock=:cash AND game=:game", price=price1, user_id=session["user_id"], game=game, cash="Cash")

    # add transaction to transaction db for history
    db.engine.execute("INSERT INTO transactions (user_id, stock, quantity, price, date, type, total, game) VALUES (:user_id, :stock, :quantity, :price, :date, :type1, :total, :game)",
                user_id=session["user_id"], total=price1, stock=quote["symbol"], type1='SOLD', quantity=round(float(shares), 2), price=quote['price'], date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),game=game)
    if float(shares) == 1:
        words = ["share", "was"]
    else:
        words = ["shares", "were"]

    return [words, shares, symbol, quote['price'], price1]


@app.route("/history",methods=["GET", "POST"])
@login_required
def history():
    """Show history of transactions"""

    if request.form.get("gamechoice"):
        session['game'] = int(request.form.get("gamechoice"))

    #NEED TO FIX: use ajax to stop every page from constant reload
    game = session['game']
    if game != 0:
        name = db.engine.execute("SELECT name FROM game WHERE gamenumber=?", game).fetchall()[0]['name']
    else:
        name = "None (personal portfolio)"
    # retrieve transactions
    transactions = db.engine.execute("SELECT * FROM transactions WHERE user_id = :user_id AND game=:game ORDER BY date DESC", user_id=session["user_id"], game=game).fetchall()
    if not transactions:
        return apology("You have no transactions to date.")

    return render_template('history.html', transactions=transactions, games=db.engine.execute("SELECT * FROM game WHERE player1 IN (:user_id) OR player2 IN (:user_id)", user_id=session['user_id']), name=name)

@app.route("/searchusers", methods=["GET", "POST"])
@login_required
def searchusers():
    if request.method == "POST":
        if request.form.get("username"):
            users = db.engine.execute("SELECT * FROM users WHERE username LIKE :search", search="%"+str(request.form.get("username"))+"%")
        return render_template("searchusers.html", users=users)
    else:
        return render_template("searchusers.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            flash('Must provide username')
            return render_template("login.html")

        # Ensure password was submitted
        elif not request.form.get("password"):
            flash('Must provide password')
            return render_template("login.html")

        # Query database for username
        rows = db.engine.execute("SELECT * FROM users WHERE username = ?", request.form.get("username")).fetchall()
        print(rows, file=sys.stdout)

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            flash('Invalid username and/or password')
            return render_template("login.html")

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]
        session['game'] = 0

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    if request.method == "POST":
        # ensure name of stock was submitted
        if not request.form.get("symbol"):
            flash('Please input a valid stock symbol.')
            return render_template("quote.html")

        # pull quote from api
        quote = lookup(request.form.get("symbol"))

        # check is valid stock name provided
        if quote == None:
            flash("Invalid Stock Symbol")
            return render_template("quote.html")
        # stock name is valid
        else:
            return render_template("quoted.html", symbol=quote["symbol"], name=quote["name"], price=quote["price"])

    # else if user reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    flash('Please fill out all fields.')
    # if user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # proceed only if all fields filled in
        if (request.form.get("username") and request.form.get("password") and request.form.get("confirmation")):
            # proceed only if passwords match
            username = request.form.get("username")
            pw = request.form.get("password")
            if pw == request.form.get("confirmation"):
                # proceed only if username is unique
                rows = db.engine.execute("SELECT * FROM users WHERE username = ?", username).fetchall()
                if len(rows) < 1:
                    # add user to database
                    x = db.engine.execute("INSERT INTO users (username, hash) VALUES (?, ?)",
                                   username, generate_password_hash(pw))
                    if not x:
                        return apology('Registration error')
                    # login user automatically and remember session
                    rows = db.engine.execute("SELECT * FROM users WHERE username = :username", username=request.form.get("username")).fetchall()
                    session["user_id"] = rows[0]["id"]
                    # redirect to home page
                    return redirect(url_for("index"))
                else:
                    flash('This username is already in use.')
            else:
                flash('Passwords do not match.')
        else:
            flash("Please fill out all fields.")
    # else if user reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")

def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
