import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True


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

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    # get user cash total
    result = db.execute("SELECT cash FROM users WHERE id=?", session["user_id"])
    cash = round(result[0]['cash'], 2)

    # pull all transactions belonging to user
    portfolio = db.execute("SELECT stock, quantity, price FROM portfolio WHERE user_id = ?", session["user_id"])

    if not portfolio:  # load in cash
        db.execute("INSERT INTO portfolio (user_id, stock) VALUES (?,?)", session["user_id"], "Cash")
        portfolio = db.execute("SELECT stock, quantity, price FROM portfolio WHERE user_id = ?", session["user_id"])

    grand_total = cash

    # determine current price, stock total value and grand total value
    for stock in portfolio:
        if stock['stock'] == "Cash":
            price = 1
            stock['quantity'] = cash
            total = cash
            stock.update({'price': price, 'total': total, 'quantity': cash})
        else:
            price = lookup(stock['stock'])['price']
            total = stock['quantity'] * price
            stock.update({'price': price, 'total': total})
            grand_total += total

    return render_template("index.html", stocks=portfolio, cash=cash, total=grand_total)

@app.route("/actionpage", methods=["GET", "POST"])
@login_required
def actionpage():
    """Get stock quote."""
    if request.method == "POST":
        # ensure name of stock was submitted
        if request.form.get("buysymbol") and request.form.get("buyshares"):
            buy(request.form.get("buysymbol"), request.form.get("buyshares"))
        
        if request.form.get("sellsymbol") and request.form.get("sellshares"):
        # pull quote from api
        quote = lookup(request.form.get("symbol"))

        # check is valid stock name provided
        if quote == None:
            flash("Invalid Stock Symbol")
            return apology("Invalid Stock Symbol")

        # stock name is valid
        else:
            return render_template("quoted.html", symbol=quote["symbol"], name=quote["name"], price=quote["price"])

    # else if user reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("quote.html")

def buy(symbol, shares):
    # if user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # ensure stock symbol and number of shares was submitted
        if not (symbol and shares):
            flash("Please input a valid stock symbol and share quantity.")
            render_template('actionpage.html')
            return False
        # ensure number of shares is valid
        if not str.isdecimal(request.form.get("shares")):
            flash('Share quantity must be a positive integer')
            return apology("Invalid share quantity")
        if float(request.form.get("shares")) <= 0 or float(request.form.get("shares")) != int(request.form.get("shares")):
            flash('Share quantity must be a positive integer.')
            return apology("Invalid share quantity")
        # pull quote
        quote = lookup(request.form.get("symbol"))

        # check is valid stock name provided
        if quote == None:
            flash('Please input a valid stock symbol.')
            return apology("Invalid stock symbol t")

        # calculate cost of transaction
        cost = round(float(request.form.get("shares")) * float(quote['price']), 2)

        # check if user has enough cash for transaction
        cashOnHand = db.execute("SELECT cash FROM users WHERE id=?", session["user_id"])
        if cost > cashOnHand[0]["cash"]:
            return apology("Insufficient Funds")
        # update cash amount in users database
        db.execute("UPDATE users SET cash=cash-:cost WHERE id=:id", cost=cost, id=session["user_id"])
        y = db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])
        c = round(y[0]['cash'], 2)

        # add transaction to transaction db for history
        add_transaction = db.execute("INSERT INTO transactions (user_id, stock, quantity, price, date, type, total) VALUES (:user_id, :stock, :quantity, :price, :date, :type1, :total)",
                                     user_id=session["user_id"], stock=quote["symbol"], type1='BOUGHT', total=cost, quantity=float(request.form.get("shares")), price=quote['price'], date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        # check if stock already owned for db organization
        rows = db.execute("SELECT quantity FROM portfolio WHERE stock=:stock", stock=quote["symbol"])
        if not rows:
            db.execute("INSERT INTO portfolio (user_id, stock, quantity) VALUES (:user_id, :stock, :quantity)",
                       stock=quote["symbol"], quantity=float(request.form.get("shares")), user_id=session["user_id"])

        # if symbol is already in portfolio, update share quantity
        else:
            db.execute("UPDATE portfolio SET quantity=quantity+:quantity WHERE stock=:stock",
                       quantity=float(request.form.get("shares")), stock=quote["symbol"])
        if float(request.form.get("shares")) == 1:
            words = ["share", "was"]
        else:
            words = ["shares", "were"]
        return render_template("buysuccess.html", word0=words[0], word1=words[1], quantity=request.form.get("shares"), symbol=quote["symbol"], name=quote["name"], price=cost, type="purchased", money=c)

    # if user reached route via GET
    else:
        return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""

    # retrieve transactions
    transactions = db.execute("SELECT * FROM transactions WHERE user_id = :user_id ORDER BY date DESC", user_id=session["user_id"])
    if not transactions:
        return apology("You have no transactions to date.")

    return render_template('history.html', transactions=transactions)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

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
            return apology("Invalid stock symbol")

        # pull quote from api
        quote = lookup(request.form.get("symbol"))

        # check is valid stock name provided
        if quote == None:
            flash("Invalid Stock Symbol")
            return apology("Invalid Stock Symbol")

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
                rows = db.execute("SELECT * FROM users WHERE username = ?", username)
                if len(rows) < 1:
                    # add user to database
                    x = db.execute("INSERT INTO users (username, hash) VALUES (?, ?)",
                                   username, generate_password_hash(pw))
                    if not x:
                        return apology('Registration error')
                    # login user automatically and remember session
                    rows = db.execute("SELECT * FROM users WHERE username = :username", username=request.form.get("username"))
                    session["user_id"] = rows[0]["id"]
                    # redirect to home page
                    return redirect(url_for("index"))
                else:
                    return apology('This username is already in use.')
            else:
                return apology('Passwords do not match.')
        else:
            return apology("Please fill out all fields.")
    # else if user reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    # if user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # ensure stock symbol and number of shares was submitted
        if not (request.form.get("symbol") and request.form.get("shares")):
            return apology("Please input a valid stock symbol and share quantity.")
        # ensure number of shares is valid
        if float(request.form.get("shares")) <= 0:
            return apology('Share quantity must be a positive real number.')
        # pull quote
        quote = lookup(request.form.get("symbol"))

        # check is valid stock name provided
        if quote == None:
            flash('Please input a valid stock symbol.')
            return apology("Invalid stock symbol")

        # check if user has enough of the stock to sell
        rows = db.execute("SELECT quantity FROM portfolio WHERE stock=:stock", stock=quote["symbol"])
        if not rows:
            return apology('You do not currently own this stock.')

        # check if enough of the stock in the portfolio
        if rows[0]["quantity"] < float(request.form.get("shares")):
            return apology('You do not have enough shares of this stock.')

        # calculate price of transaction
        price1 = round(float(request.form.get("shares")) * float(quote['price']), 2)

        db.execute("UPDATE portfolio SET quantity=quantity-:quantity WHERE stock=:stock",
                   quantity=float(request.form.get("shares")), stock=quote["symbol"])
        db.execute("UPDATE users SET cash=cash+:price WHERE id=:id", price=price1, id=session["user_id"])

        # add transaction to transaction db for history
        add_transaction = db.execute("INSERT INTO transactions (user_id, stock, quantity, price, date, type, total) VALUES (:user_id, :stock, :quantity, :price, :date, :type1, :total)",
                                     user_id=session["user_id"], total=price1, stock=quote["symbol"], type1='SOLD', quantity=float(request.form.get("shares")), price=quote['price'], date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        if float(request.form.get("shares")) == 1:
            words = ["share", "was"]
        else:
            words = ["shares", "were"]

        y = db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])
        c = round(y[0]['cash'], 2)
        return render_template("buysuccess.html", word0=words[0], word1=words[1], quantity=request.form.get("shares"), symbol=quote["symbol"], name=quote["name"], price=price1, type="sold", money=c)

    # if user reached route via GET
    else:
        stocks = db.execute("SELECT * FROM portfolio WHERE user_id = :user_id", user_id=session["user_id"])
        return render_template("sell.html", stocks = stocks)


@app.route("/addcash", methods=["GET", "POST"])
@login_required
def addcash():
    # if user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # ensure cash amount is valid
        c = round(float(request.form.get("cashInput")), 2)
        if c <= 0:
            flash('Cash quantity must be a positive real number')
            return render_template("addcash.html")

        # update cash amount in users database
        check = db.execute("UPDATE users SET cash=cash+:amt WHERE id=:id", amt=c, id=session["user_id"])
        if check:
            flash('Success')
            return render_template("addcash.html")

    else:
        return render_template("addcash.html")


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
