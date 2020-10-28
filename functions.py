import pandas as pd
import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
import numpy as np

'''
This file will hold functions used for the process of converting
the excel file to the database
'''

#reads a csv file to pandas
def readcsvtopandas(excel_file):
	df = pd.read_csv(excel_file, names=['Date','Trans','Amt'], index_col=False) #reads of csv file and creates column names
	return df

#fixes the date format
def fixdateformat(df):
	df['Date']= df['Date'].str.strip() #gets rid of white spaces
	df['Date'] =pd.to_datetime(df['Date'], format = '%m/%d/%Y') #sets the date to a standard datetime format
	df['Date']= df['Date'].dt.date #only shows the date not the timestamp which was default at 00:00:00
	
def insertdefaultGroupsColumns(df):
	df.insert(2, "Counterparty", ['N/A' for i in range(len(df))], True)
	df.insert(3, "Category", ['N/A' for i in range(len(df))], True)

def checkforduplicates(new_transaction_df, database_function):
	
	last_date_in_new_transactions = str(min(new_transaction_df['Date']))
	sql_list = database_function(last_date_in_new_transactions)	
	for i,r in new_transaction_df.iterrows():
		for row in sql_list:
			if ((str(r['Date']),r['Trans'],r['Amt'])) == row:
				yield i

#Both arguments must be lists
def keywordsmatch(description, keywords):
	if keywords is not None and description is not None:
		keywords_list = [keyword.lower() for keyword in keywords.split()]
		description_list = [word.lower() for word in description.split()]
		if set(keywords_list).intersection(description_list) == set(keywords_list):
			return True

		else:
			return False
			
	else:
		print("FAILED")

def keywordscheck(counterparty, keywords, category, transactions_without_group_df):
	for transaction_index in transactions_without_group_df.index:
		transaction_words = transactions_without_group_df.at[transaction_index, 'Trans']
		if keywordsmatch(transaction_words, keywords):
			transactions_without_group_df.at[transaction_index, 'Counterparty'] = counterparty
			transactions_without_group_df.at[transaction_index, 'Category'] = category
			
def submit_treeview_to_db(treeview, database_submit_row, database_submit_counterparty, database_create_transactions_table, database_commit):
	database_create_transactions_table()
	for item in treeview.get_children():
		row = treeview.item(item)['values']
		try:
			database_submit_counterparty(row)
		except IndexError:
			pass
		database_submit_row(row)
	database_commit()




#Deletes all the row in a treeview
def delete_treeview_rows(treeview):
	for row in treeview.get_children():
		treeview.delete(row)

#Deletes current rows and insert new rows into a Treeview based on which database function is used
def insert_new_rows_into_treeview(database_function, treeview):
	delete_treeview_rows(treeview)
	for row in database_function:
		treeview.insert('', 'end', values=row)



#GRAPHING FUNCTIONS

def graph_data(database_function):
	rows = database_function
	labels = [transaction[0] for transaction in rows]
	amounts = [round(float(transaction[1]), 2) for transaction in rows]
	#total_amount = sum(amounts)
	return labels, amounts

def pie_graph_maker(percentages, labels, title):
	fig1, ax1 = plt.subplots()
	ax1.pie(percentages, labels=labels, autopct='%1.1f%%')
	ax1.axis('equal')
	plt.title(title)
	plt.show()

def bar_graph_maker(names, amounts, title):
	y_pos = np.arange(len(names))
	plt.bar(y_pos, amounts, align='center', alpha=0.5)
	plt.xticks(y_pos, names)
	plt.ylabel("USD($)")
	plt.title(title)
	plt.show()

def pie_graph(database_function, title):
	labels, percentages = graph_data(database_function)
	#percentages_amounts = [amount/total_amount for amount in amounts]

	pie_graph_maker(percentages, labels, title)

def bar_graph(database_function, title):
	labels, amounts = graph_data(database_function)

	bar_graph_maker(labels, amounts, title)





#Functions for Counterparty/Category Page buttons - - - - - - - - - - - - - -

#This will search for all transaction with N/A counterparties
#It will take a user input for a counterparty name and keywords
#It will need to check if the counterparty name and keywords are not already taken.
#It will then need to check if there are any "N/A counterparty" transactions that that have keyword matches
#If the last two lines are True, then we add information to counterparty table, change matched transaction to have this new counterparty, update the counterparty treeview in the tab
def add_counterparty(get_trans_db_func, check_name_db_func, get_keywords_db_func, update_db_func, update_counterparty_table_func,counterparty, new_keywords):

	#list of transactions that have "N/A" for counterparty
	#uses getalltransactions_NA() from database.py

	all_na_counterparty_transactions = get_trans_db_func

	#generator used to check if a group of keywords match the entry from the user
	#getallkeywords() is the function used here which returns all the keywords recorded from the user so far
	all_keywords_gen = (keywordsmatch(keywords[0], new_keywords) for keywords in get_keywords_db_func)

	#generator used to check if there are keyword matches in the descriptions of all N/A transactions
	#all_na_counterparties_gen = (keywordsmatch(new_keywords, keywords[0]) for keywords in all_na_counterparty_transactions[1])

	list_of_matches = []
	for transaction in all_na_counterparty_transactions:
		transaction_description = transaction[1]
		if keywordsmatch(transaction_description, new_keywords):
			list_of_matches.append(transaction)

	#checks if the counterparty name is taken. If it is we return None. Uses checkifcounterpartyexists()
	if check_name_db_func(counterparty) == 1 or counterparty.isspace() or counterparty == '':
		#Error box
		tk.messagebox.showerror(title='Counterparty Name Error', message='Name is taken or is blank')
		return print("name is taken or is blank")

	#if theres a keyword match it will return True thus causing the errorbox
	elif True in all_keywords_gen:
		#Errorbox
		tk.messagebox.showerror(title='Keywords Error', message='Keywords are being used')
		return print("keywords are being used")

	#if there are no matches for this new counterparty then it raises an error
	elif len(list_of_matches)==0:
		#Error box
		tk.messagebox.showerror(title='No Matches Found', message='There are no available transactions that fit into this counterparty')
		return print("no matches")

	#passes all the checks before it
	#uses updatetransaction() and submit_counterparty_info_from_btn()
	else:
		update_counterparty_table_func(counterparty, new_keywords)
		for transaction in list_of_matches:
			update_db_func(counterparty, transaction[0], transaction[1], transaction[2])



#Choose selected counterparty in treeview
#Will bring up a messagebox if they are sure they want to delete this counterparty, will show name of counterparty, yes button, and cancel button - done
#Also say this will change all transactions with the counterparty to have "N/A" in counterparty column. - done
#If they click yes then change all transactions with the selected counterparty to "N/A" in the counterparty column
#Then remove the selected counterparty row from the counterparty table.
#Update the counterparty and category treeview to reflect this change 
#show a messagebox that says the counterparty has been deleleted and all the transactions with the counterparty have been updated

#def del_counterparty(counterparty_name, all_counterparty_trans_db_func):
	#runs alltransactions() from database file which returns all entries in Transaction Table
	#all_transactions = all_counterparty_trans_db_func(counterparty_name)
	

#Category Page Functions

#needs a category name and a counterparty that exists
#check if name exists already and if counterparty exists and is not taken by another category(or category='N/A')
#if these things are true then just add it to the table and treeview(refresh button better)
def add_category(category_name, counterparty_name, check_category_db, check_counterparty_db, check_counterparty_is_used_db, update_category_db):

	print(check_counterparty_is_used_db(counterparty_name))

	if check_category_db(category_name) == 1 or category_name.lower() == 'none':
		tk.messagebox.showerror(title='Category Name Error', message='Category name is not valid!')

	elif check_counterparty_db(counterparty_name) == 0:
		tk.messagebox.showerror(title='Counterparty Name Error', message='Counterparty does not exist!')

	elif check_counterparty_is_used_db(counterparty_name)[0][2] != 'N/A':
		tk.messagebox.showerror(title='Counterparty Name Error', message='The Counterparty is already in a category')

	else:
		update_category_db(category_name, counterparty_name)
		tk.messagebox.showinfo(title='Success', message='The Category was created!')


#need a counterparty name and a category selected
#checks if counterparty exists
#if it exists needs to check if its category = "N/A"
#if these things are true then change its category to the selected name
def add_counterparty_to_category(category_name, counterparty_name, check_counterparty_db, check_category_db, get_counterparty_info_db, update_category_db):

	if check_counterparty_db(counterparty_name) == 0: #counterparty does not exist
		tk.messagebox.showerror(title='Counterparty Name Error', message='Counterparty does not exist!')

	elif check_category_db(category_name) == 0: #category does not exist. This happens when a blank row is selected. 
		tk.messagebox.showerror(title='Category Name Error', message='Category does not exist!')

	elif get_counterparty_info_db(counterparty_name)[0][2] != 'N/A': #gets the counterparty row and checks if the category column is N/A
		tk.messagebox.showerror(title='Category Name Error', message='That Counterparty is already in another Category')

	else:
		update_category_db(category_name, counterparty_name)
		tk.messagebox.showinfo(title='Success', message='The Counterparty was added!')

#needs a counterparty name and a category seleceted
#checks if counterparty exists and if its category from the database is equal to the one selected but if its N/A then we raise an error
#if these are true then change the category to N/A and its corresponding transactions' category to N/A
def delete_counterparty_from_category(category_name, counterparty_name, check_counterparty_db, get_counterparty_info_db, update_category_db):


	if check_counterparty_db(counterparty_name) == 0: #counterparty does not exist
		tk.messagebox.showerror(title='Counterparty Name Error', message='Counterparty does not exist!')

	elif get_counterparty_info_db(counterparty_name)[0][2] == "N/A": #If the counterparty is already N/A then we don't need to do anything
		tk.messagebox.showerror(title='Category Name is N/A', message='That Counterparty is already in the default Category')

	elif category_name.lower() == "none": #If they want to remove N/A from None but this wouldn't work since None is just Null in SQL. Raise error anyway.
		tk.messagebox.showerror(title='Category Name is None', message='We cannot remove N/A from this Category')

	elif get_counterparty_info_db(counterparty_name)[0][2] != category_name: #Just in case the select event doesn't work or they're in another row
		tk.messagebox.showerror(title='Category Name Error', message='Category name did not match with Database. Try again.')

	else:
		update_category_db("N/A", counterparty_name)
		tk.messagebox.showinfo(title='Success', message='The Counterparty was deleted!')

#refresh button for category treeview
def category_refresh(tree, get_categories_db, get_counterparties_from_category_db):
	delete_treeview_rows(tree)
	for category in get_categories_db:
		current_category = category[0]
		counterparties_list = get_counterparties_from_category_db(current_category)
		treeview_row = []
		separator = ', '
		current_counterparties = separator.join(counterparties[0] for counterparties in counterparties_list)
		treeview_row.append(current_category)
		treeview_row.append(current_counterparties)
		tree.insert('', 'end', values=treeview_row)