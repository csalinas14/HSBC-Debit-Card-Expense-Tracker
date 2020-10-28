import sqlite3
import pandas as pd
from datetime import datetime

#Dictionary for name of Months to their respective number
global months 
months = {"January": "01", "February": "02", "March": "03", "April": "04", "May": "05", "June": "06", "July": "07", "August": "08", "September": "09", "October": "10", "November": "11", "December": "12"}
#This will connect to database or create one if not created
def connecttoDB():
	dbname = 'transactions'
	conn = sqlite3.connect(dbname + '.sqlite')
	return conn

conn = connecttoDB()
c = conn.cursor()
c.execute("PRAGMA foreign_keys = 1")

def commitdb():
	conn.commit()

def createtables():
	c.execute('''CREATE TABLE IF NOT EXISTS Counterparties(
			name text PRIMARY KEY,
			keywords text,
			category text
			)''')

def createtransactions():
	c.execute('''CREATE TABLE IF NOT EXISTS Transactions(
			Dates text, 
			Description text,
			Counterparty text,
			Category text,
			Amount int,
			PRIMARY KEY (Dates, Description, Amount)
			FOREIGN KEY(Counterparty) REFERENCES Counterparties(name)
			)''')

def insertNA():
	c.execute('''INSERT INTO COUNTERPARTIES VALUES('N/A', NULL, NULL)
			''')
#Create the tables we need if they don't exist yet
createtables()
try:
	insertNA()
	commitdb()
except sqlite3.IntegrityError:
	print("N/A exists already")
#finds what day is today which is used to find the current month in search function
today = datetime.today()
global datem
datem = datetime(today.year, today.month, 1).date()

#This will take any excel file and add it to our Table in SQL
#We need to create a function later that will check our excel rows for duplicates in our sql database
def exceltosql(excel_file):
	df = pd.read_csv(excel_file)
	df.to_sql(name='Transactions', con=conn, if_exists='append')

'''This will return a list of transaction from the database that are equal and after the latest date in the new transactions
being checked. This is to mimimize workload when checking for duplicates. 

'''

#The default rows that is used in the Main Tab Treeview
def defaultlist():
	c.execute('SELECT * FROM Transactions LIMIT 30')
	rows = c.fetchall()
	return rows

def alltransactions():
	c.execute('SELECT * FROM Transactions')
	rows = c.fetchall()
	return rows

#ALL QUERIES USED FOR GRAPH CREATION ------------

#Returns counterparties names and their respective percentages from total Counterparty amount
def get_all_counterparty_percentages():
	c.execute('SELECT Counterparty, (SUM(Amount)/(SELECT SUM(Amount) FROM Transactions)) * 100 FROM Transactions GROUP BY Counterparty')
	rows = c.fetchall()
	return rows
#Same as above but instead of counterparties it is for categories
def get_all_category_percentages():
	c.execute('SELECT Category, (SUM(Amount)/(SELECT SUM(Amount) FROM Transactions)) * 100 FROM Transactions GROUP BY Category')
	rows = c.fetchall()
	return rows

def get_all_counterparty_amounts():
	c.execute('SELECT Counterparty, SUM(Amount) FROM Transactions GROUP BY Counterparty ORDER BY Amount ASC')
	rows = c.fetchall()
	return rows

def get_all_category_amounts():
	c.execute('SELECT Category, SUM(Amount) FROM Transactions GROUP BY Category ORDER BY Amount ASC')
	rows = c.fetchall()
	return rows




#Searches the database for specific counterparties
#Uses month and year as parameters for searching
#There is a special case for month called "All" where we return either every counterparty result or yearly results
def search_counterparty_db(month, year, counterparty='N/A'):
	if month == 'All' and (year == '' or year.isspace()==True):
		c.execute('SELECT * FROM Transactions WHERE COUNTERPARTY = ?', (counterparty,))
	elif month == 'All':
		c.execute('SELECT * FROM Transactions WHERE strftime("%Y", DATES) = ? AND COUNTERPARTY = ?', (year, counterparty))
	else:
		number_month = months[month]
		c.execute('SELECT * FROM Transactions WHERE strftime("%m", DATES) = ? AND strftime("%Y", DATES) = ? AND COUNTERPARTY = ?', (number_month, year, counterparty))
	rows = c.fetchall()
	return rows

#Same as the above function but we replace counterparty with category
def search_category_db(month, year, category='N/A'):
	if month == 'All' and (year == '' or year.isspace()==True):
		c.execute('SELECT * FROM Transactions WHERE CATEGORY = ?', (category,))
	elif month == 'All':
		c.execute('SELECT * FROM Transactions WHERE strftime("%Y", DATES) = ? AND CATEGORY = ?', (year, category))
	else:
		number_month = months[month]
		c.execute('SELECT * FROM Transactions WHERE strftime("%m", DATES) = ? AND strftime("%Y", DATES) = ? AND CATEGORY = ?', (number_month, year, category))
	
	rows = c.fetchall()
	return rows

def gettransactionafterdate(last_date):
	
	c.execute('SELECT * FROM Transactions WHERE DATES >= ?', (last_date,))
	list_of_rows_after_date = c.fetchall()
	sql_list = [row for row in list_of_rows_after_date]
	return sql_list

def getduplicatedate(your_date):
	c.execute('SELECT DATES, DESCRIPTION, AMOUNT FROM Transactions WHERE DATES >= ?', (your_date,))
	list_of_rows_after_date = c.fetchall()
	sql_list = [row for row in list_of_rows_after_date]
	return sql_list

#Searches for the counterparties, keywords, and category from the Counterparty Table
#Does not include 'N/A' which is the default name for counterparty if not changed
def getcounterparties():
	c.execute('SELECT * FROM Counterparties WHERE NAME != "N/A"')
	rows = c.fetchall()
	return rows

def getcounterparties_na():
	c.execute('SELECT * FROM Counterparties WHERE NAME = "N/A"')
	rows = c.fetchall()
	return rows

def getallcounterparties():
	c.execute('SELECT * FROM Counterparties')
	rows = c.fetchall()
	return rows

def getallcategories():
	c.execute('SELECT DISTINCT CATEGORY FROM Counterparties')
	rows = c.fetchall()
	return rows

def get_counterparties_for_category(category_name):
	if category_name == None:
		c.execute('SELECT NAME FROM COUNTERPARTIES WHERE CATEGORY IS NULL')
	else:
		c.execute('SELECT NAME FROM COUNTERPARTIES WHERE CATEGORY=?',(category_name,))
	rows = c.fetchall()
	return rows

def getonecounterparty(counterparty_name):
	c.execute('SELECT * FROM Counterparties WHERE NAME = ?', (counterparty_name,))
	rows = c.fetchall()
	return rows

''''These Functions check if a counterparty or category name is taken'''

#Checks if counterparty name is taken. If it is, returns 1. Else it returns 0
def checkifcounterpartyexists(counterparty_name):
	c.execute('SELECT EXISTS(SELECT * FROM COUNTERPARTIES WHERE NAME = ?)',(counterparty_name,))
	[exists] = c.fetchone()
	return exists

#Checks if category name is taken. If it is, returns 1. Else it returns 0
def checkifcategoryexists(category_name):
	c.execute('SELECT EXISTS(SELECT * FROM COUNTERPARTIES WHERE CATEGORY = ?)',(category_name,))
	[exists] = c.fetchone()
	return exists


#Returns all keywords from the Counterparty Table
def getallkeywords():
	c.execute('SELECT KEYWORDS FROM COUNTERPARTIES')
	rows = c.fetchall()
	return rows

def submit_row_to_db(treeview_row):
	date = treeview_row[0]
	description = treeview_row[1]
	counterparty = treeview_row[2]
	category = treeview_row[3]
	amount = treeview_row[4]
	c.execute('INSERT INTO TRANSACTIONS VALUES(?,?,?,?,?)', (date, description, counterparty, category, amount))

def submit_counterparty_info(treeview_row):
	counterparty = treeview_row[2]
	category = treeview_row[3]
	keywords = treeview_row[5]
	c.execute('INSERT INTO COUNTERPARTIES VALUES(?,?,?)', (counterparty, keywords, category))


#Functions used exclusively for the "Add Counterparty" button -------------------

def getalltransactions_NA():
	c.execute('SELECT Dates, Description, Amount FROM Transactions WHERE Counterparty = "N/A"')
	rows = c.fetchall()
	return rows




#update a transaction in the database
def updatetransaction(counterparty, date, description, amount):
	c.execute('UPDATE Transactions SET counterparty=? WHERE Dates=? AND Description=? AND Amount=?', (counterparty, date, description, amount))
	commitdb()
#similar to submit_counterparty_into but inputs are taken differently
#this will give the default value for category
def submit_counterparty_info_from_btn(counterparty, keywords):
	c.execute('INSERT INTO COUNTERPARTIES VALUES(?,?,"N/A")', (counterparty, keywords))
	commitdb()

#Functions used for "Delete Counterparty button"
def all_counterparties_trans(counterparty_name):
	#c.execute('SELECT * FROM Transactions WHERE Counterparty=?',(counterparty_name,))
	c.execute('UPDATE Transactions SET Counterparty="N/A", Category="N/A" WHERE Counterparty =?', (counterparty_name,))
	c.execute('DELETE FROM COUNTERPARTIES WHERE Name=?', (counterparty_name,))
	commitdb()



#Category Page
#This is used for "Add Category" , "Add/Delete a Counterparty from Category" Button
def updatecategory(category_name, counterparty_name):
	c.execute('UPDATE COUNTERPARTIES SET CATEGORY = ? WHERE NAME = ?', (category_name, counterparty_name))
	c.execute('UPDATE TRANSACTIONS SET CATEGORY = ? WHERE COUNTERPARTY=?', (category_name, counterparty_name))
	commitdb()

#This is used for the "Delete Category" Button
def delete_a_category(category_name):
	c.execute('UPDATE COUNTERPARTIES SET CATEGORY = "N/A" WHERE CATEGORY = ?', (category_name,))
	c.execute('UPDATE TRANSACTIONS SET CATEGORY = "N/A" WHERE CATEGORY = ?', (category_name,))
	commitdb()


if __name__ == '__main__':
	conn = connecttoDB()
	c = conn.cursor()
	for row in c.execute('SELECT * FROM Transactions'):
		print(row)