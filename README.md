# HSBC-Debit-Card-Expense-Tracker
## Introduction!
Hello! This is my first project. I will be updating this readme in the future to better explain how this app works. The general idea of it is that it takes my bank statements that are in excel form and adds it to a database. The database sends the data to the user and displays it in a GUI I created. The user can do several things with the app and all their transactions from the bank statement. The main purpose is to group transactions into "Counterparties" i.e. Amazon, Spotify, any vendor really. We may also group the counterparties into "Categories" which are just groups of counterparties. Once you created counterparties and categories, the app will automatically recognize if a transaction belongs in a certain counterparty/category based on keywords the user specifies for each counterparty. An example of this is just "Amazon" whenever we want the app to recognize a counterparty called "Amazon". Once you set up information you may see it displayed in the app. Lastly there is also a part that graphs these counterparties and categories. 

The aim of this project was to create something useful to me but also challenge myself and learn new things. I got hands on experience with a GUI which was the tkinter library in this case. I also got experience using databases by making use of the SQLite library. I also learned how to take a source of data and turn it into something I can use. 

All my code was done in Python 3. New libraries I learned to use are Tkinter, SQLite3, and abit of OS and datetime.

The app file contains most of the code. Mostly tkinter and maybe references to functions and database files when needed.
The database file has the code that makes callback to our database.
The functions file contains functions that are used in the app file. 
The test excel file is some sample data of what the HSBC banking history would look like.