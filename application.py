import os

from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
import datetime 
from flask_sqlalchemy import SQLAlchemy
import sys

from helpers import apology, login_required, lookup, usd, historicalPlot




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

    #cash = round(db.engine.execute("SELECT * FROM portfolio WHERE stock=:cash AND user_id=:user_id AND game=:game", cash="Cash",user_id=session["user_id"], game=game).fetchall()[0]['quantity'], 2)
    x = calculate_portfolio_value(portfolio)

    return render_template("index.html", games=db.engine.execute("SELECT * FROM game WHERE player1 IN (:user_id) OR player2 IN (:user_id)", user_id=session['user_id']), name=name, stocks=x[1], total=x[0], game=game) #need to implement game choice

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
        return render_template("actionpage.html", stocks = db.engine.execute("SELECT * FROM portfolio WHERE user_id = :user_id AND quantity > 0 AND game=:game", user_id=session["user_id"], game=session['game']),games=db.engine.execute("SELECT * FROM game WHERE player1 IN (:user_id) OR player2 IN (:user_id)", user_id=session['user_id']),name=name)

    # else if user reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("actionpage.html", stocks = db.engine.execute("SELECT * FROM portfolio WHERE user_id = :user_id AND quantity > 0 AND game=:game", user_id=session["user_id"], game=session['game']), games=db.engine.execute("SELECT * FROM game WHERE player1 IN (:user_id) OR player2 IN (:user_id)", user_id=session['user_id']))

@app.route("/gamescreen", methods=["GET", "POST"])
@login_required
def gamescreen():   
    sentinvites = db.engine.execute("SELECT * FROM game WHERE player1 IN (:user_id) AND initialized=0 AND finished=0", user_id=session['user_id']).fetchall() 
    sgame = []
    for games in sentinvites: 
        game = dict(games)
        opponent = str(db.engine.execute("SELECT * FROM users WHERE id=?", game['player2']).fetchall()[0]['username'])
        duration = str(datetime.timedelta(days=((int(game['years']) * 365) + int(game['days'])), weeks=int(game['weeks']))).split(",")[0]
        game.update({'opponent': opponent})
        game.update({'duration': duration})
        sgame.append(game)

    pastgames = db.engine.execute("SELECT * FROM game WHERE (player1 IN (:user_id) OR player2 IN (:user_id)) AND initialized=1 AND finished=1", user_id=session['user_id']).fetchall()
    pgame = []
    for games in pastgames:
        game = dict(games)
        wu = db.engine.execute("SELECT * FROM users WHERE id=?", game['winner']).fetchall()
        if len(wu) > 0:
            wu = wu[0]['username']
        if not wu: #winner is 0 when tie 
            wu = "Tie"
        game.update({'wu':wu})
        pgame.append(game)

    if request.method == "POST":
        if request.form.getlist("accept"):
            accepts = request.form.getlist("accept")
            current = datetime.datetime.now()
            for accept in accepts: 
                db.engine.execute("UPDATE game SET initialized=1, startdate=:start WHERE gamenumber=:game", start=current.strftime("%Y-%m-%d %H:%M:%S"), game=int(accept))
            #cgame = list(filter(lambda i: i['id'] != 2, test_list)) 
        currentgames = db.engine.execute("SELECT * FROM game WHERE (player1 IN (:user_id) OR player2 IN (:user_id)) AND initialized=1 AND finished=0", user_id=session['user_id']).fetchall()
        for game in currentgames:
            timeRemaining(game['gamenumber'])
        currentgames = db.engine.execute("SELECT * FROM game WHERE (player1 IN (:user_id) OR player2 IN (:user_id)) AND initialized=1 AND finished=0", user_id=session['user_id']).fetchall() 
        cgame = []
        for games in currentgames: 
            game = dict(games)
            if int(game["player1"]) == int(session['user_id']):
                opponent = str(db.engine.execute("SELECT * FROM users WHERE id=?", game["player2"]).fetchall()[0]['username'])
            else: 
                opponent = str(db.engine.execute("SELECT * FROM users WHERE id=?", game["player1"]).fetchall()[0]['username'])
            game.update({'opponent': opponent})
            cgame.append(game)
        gameinvites = db.engine.execute("SELECT * FROM game WHERE player2 IN (:user_id) AND initialized=0 AND finished=0", user_id=session['user_id']).fetchall() 
        igame = []
        for games in gameinvites: 
            game = dict(games)
            opponent = str(db.engine.execute("SELECT * FROM users WHERE id=?", game["player1"]).fetchall()[0]['username'])
            duration = str(datetime.timedelta(days=((int(game['years']) * 365) + int(game['days'])), weeks=int(game['weeks']))).split(",")[0]
            game.update({'opponent': opponent})
            game.update({'duration': duration})
            igame.append(game)
        return render_template("gamescreen.html", currentgames=cgame, gameinvites=igame, sentvites=sgame, pastgames=pgame)

    # else if user reached route via GET (as by clicking a link or via redirect)
    else:
        currentgames = db.engine.execute("SELECT * FROM game WHERE (player1 IN (:user_id) OR player2 IN (:user_id)) AND initialized=1 AND finished=0", user_id=session['user_id']).fetchall()
        for game in currentgames:
            timeRemaining(game['gamenumber'])
        currentgames = db.engine.execute("SELECT * FROM game WHERE (player1 IN (:user_id) OR player2 IN (:user_id)) AND initialized=1 AND finished=0", user_id=session['user_id']).fetchall() 
        cgame = []
        for games in currentgames: 
            game = dict(games)
            if int(game["player1"]) == int(session['user_id']):
                opponent = str(db.engine.execute("SELECT * FROM users WHERE id=?", game["player2"]).fetchall()[0]['username'])
            else: 
                opponent = str(db.engine.execute("SELECT * FROM users WHERE id=?", game["player1"]).fetchall()[0]['username'])
            game.update({'opponent': opponent})
            cgame.append(game)
        gameinvites = db.engine.execute("SELECT * FROM game WHERE player2 IN (:user_id) AND initialized=0 AND finished=0", user_id=session['user_id']).fetchall() 
        igame = []
        for games in gameinvites: 
            game = dict(games)
            opponent = str(db.engine.execute("SELECT * FROM users WHERE id=?", game["player1"]).fetchall()[0]['username'])
            duration = str(datetime.timedelta(days=((int(game['years']) * 365) + int(game['days'])), weeks=int(game['weeks']))).split(",")[0]
            game.update({'opponent': opponent})
            game.update({'duration': duration})
            igame.append(game)
        return render_template("gamescreen.html", currentgames=cgame, gameinvites=igame, sentvites=sgame, pastgames=pgame)

@app.route("/newgame", methods=["GET", "POST"])
@login_required
def newgame():
    if request.method == "POST":
        if request.form.getlist("invite"):
            invites = request.form.getlist("invite")
            for invite in invites:
                return render_template("newgame.html", uname=str(invite))
        # ensure name of stock was submitted
        if not ((request.form.get("player2")) and (request.form.get("gamename")) and (request.form.get("days") or request.form.get("years") or request.form.get("weeks"))):
            flash('Please input a game name, duration, and second player')
            return render_template("newgame.html")
        startingcash = request.form.get("startingcash")
        if not startingcash:
            startingcash = 10000 
        days = request.form.get("days")
        if not days:
            days = 0
        days = int(days)
        years = request.form.get("years")
        if not years:
            years = 0
        years = int(years)
        weeks = request.form.get("weeks")
        if not weeks:
            weeks = 0
        weeks = int(weeks)

        player2uname = request.form.get("player2")
        gamename = request.form.get("gamename")
        rows = db.engine.execute("SELECT * FROM users WHERE username = ?", request.form.get("player2")).fetchall()
        if len(rows) < 1:
            flash("invalid username")
            return render_template("newgame.html")
        player2=db.engine.execute("SELECT * FROM users WHERE username=?",player2uname).fetchall()[0]['id']
        db.engine.execute("INSERT INTO game (player1, player2, name, initialized, starting_cash, years, weeks, days, finished) VALUES (:player1, :player2, :name, :initialized, :startingcash, :years, :weeks, :days, :finished)",
                  player1=session["user_id"], player2=player2, initialized=0, name=gamename, startingcash=startingcash, years=years, weeks=weeks, days=days, finished=0)
        gameList=db.engine.execute("SELECT * FROM game WHERE player1=:player1 AND player2=:player2 AND name=:gamename AND initialized=:init AND starting_cash=:startingcash AND years=:years AND weeks=:weeks AND days=:days AND finished=0", 
                                   player1=session["user_id"], player2=player2, gamename=gamename, init=0, startingcash=startingcash, years=years, weeks=weeks, days=days).fetchall()
        game = int(gameList[len(gameList) - 1]['gamenumber']) #in case of duplicate games with the exact same parameters, get most recent
        db.engine.execute("INSERT INTO portfolio (user_id, stock, quantity, price, game) VALUES (:user_id,:stock,:startingcash, :dollar, :game)", user_id=session["user_id"], stock="Cash", startingcash=startingcash, dollar=1, game=game)
        db.engine.execute("INSERT INTO portfolio (user_id, stock, quantity, price, game) VALUES (:user_id,:stock,:startingcash, :dollar, :game)", user_id=player2, stock="Cash", startingcash=startingcash, dollar=1, game=game)


        # stock name is valid
        return render_template("newgame.html")

    # else if user reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("newgame.html")

def timeRemaining(game):
    current = datetime.datetime.now() #.strftime("%Y-%m-%d")
    g = db.engine.execute("SELECT * FROM game WHERE gamenumber=?", game).fetchall()[0]
    start = datetime.datetime.strptime(str(g['startdate']), "%Y-%m-%d %H:%M:%S") #convert date string in db to datetime obj

    duration = datetime.timedelta(days=((int(g['years']) * 365) + int(g['days'])), weeks=int(g['weeks']))
    diff = current - start #timedelta obj
    togo = duration - diff 
    #return(elapsed)
    if togo > datetime.timedelta(seconds=1):
        db.engine.execute("UPDATE game SET timeRemaining=:time WHERE gamenumber=:game", time=str(togo).split(".")[0], game=game)
    else: 
        db.engine.execute("UPDATE game SET timeRemaining=0, finished=1 WHERE gamenumber=:game", game=game)
        player1 = int(db.engine.execute("SELECT * FROM game WHERE gamenumber = ?", game).fetchall()[0]['player1'])
        player2 = int(db.engine.execute("SELECT * FROM game WHERE gamenumber = ?", game).fetchall()[0]['player2'])
        port1 = db.engine.execute("SELECT * FROM portfolio WHERE user_id=:user_id AND game=:game", user_id=player1, game=game).fetchall()
        port2 = db.engine.execute("SELECT * FROM portfolio WHERE user_id=:user_id AND game=:game", user_id=player2, game=game).fetchall()
        tot1 = calculate_portfolio_value(port1)[0]
        tot2 = calculate_portfolio_value(port2)[0]
        db.engine.execute("UPDATE game SET p1total=:tot1, p2total=:tot2 WHERE gamenumber=:game", tot1=tot1, tot2=tot2, game=game)

        if tot1 > tot2:
            winner = player1
        elif tot2 > tot1: 
            winner = player2
        else: 
            winner = 0 #if there's a tie, winner will be set to 0 
        db.engine.execute("UPDATE game SET winner=:winner WHERE gamenumber=:game", game=game, winner=winner)
        if winner:
            db.engine.execute("UPDATE users SET wins=wins+1 WHERE id=:winner", winner=winner)

def calculate_portfolio_value(portfolio):
    grand_total = 0
    # determine current price, stock total value and grand total value
    stockDictList = []
    for stocks in portfolio:
        stock = dict(stocks)
        if stock['stock'] == "Cash":
            total = stock['quantity'] 
            stock.update({'total': total})
            grand_total += total
            stockDictList.append(stock)
        else:
            quantity = round(stock['quantity'], 2)
            if quantity > 0.1: #in case of float errors
                price = lookup(stock['stock'])['price']
                total = stock['quantity'] * price
                stock.update({'price': price, 'total': total, 'quantity': quantity})
                grand_total += total
                stockDictList.append(stock) 
    return [grand_total, stockDictList]
    


def buy(symbol, shares, game):
    if not (symbol and shares):
        flash("Please input a valid stock symbol and share quantity.")
        return []
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
                                 user_id=session["user_id"], stock=quote["symbol"], type1='BOUGHT', total=cost, quantity=float(shares), price=quote['price'], date=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), game=game)

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
    return [words, round(quote['price'], 2), cost] #TODO: USE WORDS IN CUSTOM FLASH. same goes for sell

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
                user_id=session["user_id"], total=price1, stock=quote["symbol"], type1='SOLD', quantity=round(float(shares), 2), price=quote['price'], date=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),game=game)
    if float(shares) == 1:
        words = ["share", "was"]
    else:
        words = ["shares", "were"]

    return [words, shares, symbol, quote['price'], price1]

@app.route("/profile",methods=["GET", "POST"])
@login_required
def profile():
    user = db.engine.execute("SELECT * FROM users WHERE id=:user_id", user_id=session['user_id']).fetchall()[0]
    if not user['wins']: 
        db.engine.execute("UPDATE users SET wins=0 WHERE id=:user_id", user_id=session['user_id'])
        user = db.engine.execute("SELECT * FROM users WHERE id=:user_id", user_id=session['user_id']).fetchall()[0]
    if request.method == "POST":
        if request.form.get("password"):
            if check_password_hash(user['hash'], request.form.get("password")):
                # if not (request.form.get("username") or request.form.get("newPassword") or request.form.get("desc")):
                #     flash("Please select an action!") people may want to set their description to be blank 
                db.engine.execute("UPDATE users SET description=:desc WHERE id=:user_id", desc=request.form.get("desc"), user_id=session['user_id'])
                if request.form.get("username"):
                    rows = db.engine.execute("SELECT * FROM users WHERE username = ?", request.form.get("username")).fetchall()
                    if (len(rows) < 1):
                        db.engine.execute("UPDATE users SET username=:uname WHERE id=:user_id", uname=request.form.get("username"), user_id=session['user_id'])
                        flash("Successfully updated username.")
                    else: 
                        flash("That username is already taken.")
                if request.form.get("newPassword"):
                    pw = generate_password_hash(request.form.get("newPassword"))
                    db.engine.execute("UPDATE users SET hash=:pw WHERE id=:user_id", pw=pw, user_id=session['user_id'])
                    flash("Successfully updated password.")
                user = db.engine.execute("SELECT * FROM users WHERE id=:user_id", user_id=session['user_id']).fetchall()[0]
            else: 
                flash("Incorrect password.")
        return render_template("profile.html", user=user)    
    else: 
        return render_template("profile.html", user=user)

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

    return render_template('history.html', transactions=transactions, games=db.engine.execute("SELECT * FROM game WHERE player1 IN (:user_id) OR player2 IN (:user_id) AND initialized=1", user_id=session['user_id']), name=name)

@app.route("/searchusers", methods=["GET", "POST"])
@login_required
def searchusers(): #TODO: Make this a 'get' with query strings, like other searches 
    if request.method == "POST":
        if request.form.get("username"):
            users = db.engine.execute("SELECT * FROM users WHERE username LIKE :search", search="%"+str(request.form.get("username"))+"%")
            return render_template("searchusers.html", users=users)
        else:
            return render_template("searchusers.html")
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
            plot = historicalPlot(request.form.get("symbol"))
            return render_template("quoted.html", symbol=quote["symbol"], name=quote["name"], price=quote["price"], plot=plot)

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
                    x = db.engine.execute("INSERT INTO users (username, hash, wins, description) VALUES (?, ?, ?, ?)",
                                   username, generate_password_hash(pw), 0, "")
                    if not x:
                        flash('Registration error')
                        return render_template("register.html")
                    # login user automatically and remember session
                    rows = db.engine.execute("SELECT * FROM users WHERE username = :username", username=request.form.get("username")).fetchall()
                    session["user_id"] = rows[0]["id"]
                    session['game'] = 0
                    # redirect to home page
                    return redirect(url_for("index"))
                else:
                    flash('This username is already in use.')
            else:
                flash('Passwords do not match.')
        else:
            flash("Please fill out all fields.")
        return render_template("register.html")
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
