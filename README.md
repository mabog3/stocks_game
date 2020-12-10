In order to run this application, either run Flask in your local environment after setting environment variable API_KEY to a valid IEX API key, or visit the following link: https://aqueous-wave-92474.herokuapp.com/login. Note that this Heroku link will likely respond very slowly as only free hosting options were chosen. 
Once the application is running, the user should either log in at the login page by entering their username and password and clicking "sign in," or they should navigate to the registration page by clicking the button that says "register". On the register page, the user should register by inputting a desired username and password, and confirming the password. The webpage will notify the user if the passwords do not match or do not fulfill minimum requirements, and after clicking "register" on the bottom, the user will be informed if their username is already taken. 
After successfully registering or logging in, the user will be taken to their Portfolio page. The text following "Current game:" at the top of the screen indicates the game for which the user is viewing their stock portfolio. Newly registered users are not part of any active games, so only the "No Game" option will appear in the dropdown below. This 'personal portfolio' simply allows the user to play around with simulted stock trading, buying and selling stocks without comparison to any other players, or a time limit. 
To begin a game, the user should click "games" on the top navigation bar. On this screen, the user can see all of their current games, as well as details such as their opponent, the time left in the game, and the name of the game. Below that, the user can view all of the game invites they have recieved. If the user has a game invite, it will appear along with details about the opponent that proposed the game, the game's name, and the proposed duration. Also, a checkbox will appear at the right. If the user checks one or more check boxes and then clicks 'accept checked invites' at the bottom, then all of the 'game invitations' corresponding to the checked boxes will be accepted, and these games will begin and begin their countdowns (and will be visible in 'current games' on the game page). 
In order to send a game invite, the user should press 'new game' on top of the game page, and then fill out the form that appears; of the 'Duration' inputs in the right column, at least one time value must have an input. Also, the 'game name' and 'opponent' inputs must have an input; if no user with the inputted username exists, the webpage will flash this to the user. A cash starting value can also be entered, though this is not required and is $10000 by default. After clicking 'send invite' the user will have sent an invite to the other player, and will see the game appear in 'sent invites' on the games page. 
'Past games' on the webpage inform a user of the results of their past games. 
In order to search for a user, the user should click 'search' in the navigation bar on the top, enter 'search' into the search bar on the page that appears, then click the magnifying glass button on the right. Any username containing the string the user input will appear at bottom, and clicking on any result will expand more information about that user, such as the number of times they have won a game and their description. Pressing the 'invite' button for a user search result will also take the user to th new game page, except with the other user's name already filled in as opponent. 
On the 'action' page found on the nav bar at the top, the user can buy or sell stock by inputting the stock symbol, or choosing it from already owned stocks (respectively), entering the amount of shares, and clicking Buy or Sell. The user can also choose what game to target this operation on by using the 'Choose game' dropdown. The No Game option will also see an "add cash" action appear, where the user can input a cash amount they want added only to their personal portfolio. 
Pressing "history" on the navigation bar will allow the user to see the transaction history for the game chosen via the drop-down. 
Clicking 'profile' on the top right will allow the user to modify their username, password, and/or description, by entering the desired quantity in the appropriately-labeled box, entering their (old) password, and clicking "submit changes". 
"Quote", which can be accessed at the top of the navbar, allows the user to input  valid stock symbol and see the real-time price of the stock as well as an interactive graph to see trends of that stock's price over time. This graph can be zoomed in on by dragging the selector at the bottom, or selecting a square region on the graph itself.
A game is won or lost when the time of its duration elapses. Whichever player has a higher-valued portfolio when the game ends will be the winner, and this will be displayed on the Games page in the 'past games' section. 