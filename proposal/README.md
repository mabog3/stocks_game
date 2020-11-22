# Proposal

## What will (likely) be the title of your project?

Stock Market Competition

## In just a sentence or two, summarize your project. (E.g., "A website that lets you buy and sell stocks.")

A website where users can simulate stock trading and compete with other users in 'games' that they can configure to see whose stock picks would have done betterin real life.

## In a paragraph or more, detail your project. What will your software do? What features will it have? How will it be executed?

The web app will have a Flask backend and a JS/CSS (with Bootstrap)/HTML front end, but if possible I will implement a React front end to allow for more dynamic and interactive web pages,
as well as more efficient loading. It will include similar buy/sell/stock quote mechanics as Finance, but it will also allow users to enter into "games"
with other users, and let users execute all of those functions relative to their chosen game (i.e. if I'm playing games with both Alice and Bob, I can buy 20 shares of
AAPL in my game with Bob without affecting my game with Alice). To enable this, each user will be able to search for other users and invite them to games, which will be
won/lost based on who has the highest-value portfolio after a chosen amount of time.

## If planning to combine CS50's final project with another course's final project, with which other course? And which aspect(s) of your proposed project would relate to CS50, and which aspect(s) would relate to the other course?

None

## If planning to collaborate with 1 or 2 classmates for the final project, list their names, email addresses, and the names of their assigned TFs below.

None

## In the world of software, most everything takes longer to implement than you expect. And so it's not uncommon to accomplish less in a fixed amount of time than you hope.

### In a sentence (or list of features), define a GOOD outcome for your final project. I.e., what WILL you accomplish no matter what?

Users can initialize a game with 1 other user, with the game only initializing after the recipient accepts the request
When initializing a game, users can set the parameters of that game (time until 'winner' is declared, amount of starting cash, etc.)
Users can view game invitiations they've recieved, along with the parameters of the proposed game, and accept or decline
Users can view their current games, and the status of their portfolio (and their competitor's, if allowed) in each game
Buy/sell is specific to games, and a user is able to choose the game they want to act on
Improved UI and visual style compared to CS50 Finance (not 100% certain what should be improved at this point; will solicit suggestions from classmates after inmplementing backend)
'Winner' will be declared after designated time, and a user can see how many games they've won/lost

### In a sentence (or list of features), define a BETTER outcome for your final project. I.e., what do you THINK you can accomplish before the final project's deadline?

support for options trading as well as stocks
Users can view past games, and their results
users have full 'profies' that other users can view and they can edit with info
More advanced game options - i.e. users can enable/disable options trading, buying certain stocks/options, change the win condition from just time elapsed, more that I think of
Leaderboard for users (most games won, highest portfolio % growth, etc.)
More detailed 'quote'-esque page, with summary of that stock's recent movements, and the stock exchange at large

### In a sentence (or list of features), define a BEST outcome for your final project. I.e., what do you HOPE to accomplish before the final project's deadline?

Implement the front end in React instead of flask/HTML only
Support for games with an arbitrary number of players, not just 2
Support for various different stock exchanges
Support for 'friends' system where users can send/accept friend request and view their friends, and a user can make themselves open to all game invitations, or just open to invitations from "friends"

## In a paragraph or more, outline your next steps. What new skills will you need to acquire? What topics will you need to research? If working with one of two classmates, who will do what?

I will first research SQLAlchemy and how to use it in order to step away from CS50 SQL 'training wheels', and also determine how to best structure the database in terms of
supporting the large amount of data that will be associated with each user. I'll also research how to implement (or potentially create) APIs that enable some of my desired features,
such as options trading and different stock exchanges. I'll also research how to combine Flask and React, specifically how to ensure the Flask back end changes React component state so
that desired data are displayed on the React-generated webpage. I'll also research how to make some basic UI improvements, such as flashing an error of my choice when the user inputs some incorrect value
instead of immediately returning an error page, which is inconvenient. However, first I will implement the bare-bones "game" structure, adapting some of the primitive functionality I built for CS50
Finance (i.e. Buy, Sell, Quote), likely by creating a new table for games and adding a column for the current game in the portfolio and transaction history tables I built, and going from there.
