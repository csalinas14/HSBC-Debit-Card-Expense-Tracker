import database
import expensetracker
import functions
from tkinter import *
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime
import os


months = ["All","January", 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']

if __name__ == '__main__':
	
	root = Tk()
	root.title("HSBC Debit Card Expense Tracker")
	#root.geometry("800x700")

	#This is a fix I looked up involving tkinter tag_configure and python 3.7+
	def fixed_map(option):
	# Returns the style map for 'option' with any styles starting with
	# ("!disabled", "!selected", ...) filtered out

	# style.map() returns an empty list for missing options, so this should
	# be future-safe
		return [elm for elm in style.map("Treeview", query_opt=option) if elm[:2] != ("!disabled", "!selected")]

	style = ttk.Style()
	style.map("Treeview", foreground=fixed_map("foreground"), background=fixed_map("background"))

	style.map('TCombobox', fieldbackground=[('readonly','white')])
	style.map('TCombobox', selectbackground=[('readonly', 'white')])
	style.map('TCombobox', selectforeground=[('readonly', 'black')])



	"""------------------------------------------------------------------------------------------------------------------------------------------------"""

	'''New Window'''
	

	#Upload function. Creates a new window to handle new entries from csv to sqlite3. Gives users the option to change counterparty/keywords of new entries

	def upload():
		global columns
		#Opens current directory and asks for a CSV file to upload
		filename = filedialog.askopenfilename(initialdir=os.getcwd(), title="Upload CSV", filetypes=(("CSV File", "*.csv"),("All Files", "*.*")))
		
		#Creates a new window
		new_window = Toplevel(root)
		new_window.title("New Transactions")

		#Creates a Frame around our Treeview
		wrapper2 = LabelFrame(new_window, text="Transactions List")
		wrapper2.grid(row=0, column=0, columnspan=2)

		wrapper3 = LabelFrame(new_window, text="Current Counterparty Selected")
		wrapper3.grid(row=1, column=0, sticky=W, ipadx=100, ipady=40, padx=20)

		wrapper4 = LabelFrame(new_window, text="Enter Counterparty Name")
		wrapper4.grid(row=1, column=1)

		#New Treeview in the new Window
		global new_transactions_treeview
		new_transactions_columns = ['Date', 'Description', 'Counterparty', 'Category', 'Amt', 'Keywords']
		new_transactions_treeview = ttk.Treeview(wrapper2, columns=new_transactions_columns, show="headings")
		new_transactions_treeview.column("Date", width=80)
		new_transactions_treeview.column("Description", width=600)
		new_transactions_treeview.column("Counterparty", width=150)
		new_transactions_treeview.column("Category", width=150)
		new_transactions_treeview.column("Amt", width=80)
		new_transactions_treeview.column("Keywords", width=80)
		for col in new_transactions_columns:
			new_transactions_treeview.heading(col, text=col)
		new_transactions_treeview.pack(side="left", fill="y")

		new_transactions_treeview.bind('<<TreeviewSelect>>', lambda event: select_new_transaction(event, new_transactions_treeview))


		#Scrollbar
		scrollbar = Scrollbar(wrapper2, orient='vertical')
		scrollbar.configure(command=new_transactions_treeview.yview)
		scrollbar.pack(side="right", fill="y")
		new_transactions_treeview.config(yscrollcommand=scrollbar.set)

		#Read and fix csv file and insert into treeview
		new_transactions_df = functions.readcsvtopandas(filename)
		functions.fixdateformat(new_transactions_df)
		functions.insertdefaultGroupsColumns(new_transactions_df)

		try:
			for index in functions.checkforduplicates(new_transactions_df, database.getduplicatedate):
				new_transactions_df.drop([index], inplace=True)
		except database.sqlite3.OperationalError:
			#this error will pop if its a first time user so we just pass
			pass
		finally:
			#This will update the dateframe with the correct groups depending on keyword matches
			counterparty_rows = database.getcounterparties()

			#THIS NEEDS TO CHANGE TO REFLECT CASES LIKE AMAZON WEB SERVICES AND AMAZON 
			
			#for counterparty, keywords, category in counterparty_rows:
				#functions.keywordscheck(counterparty, keywords, category, new_transactions_df)

			#This block of code is used to find all the counterparties that will match with new transactions based on keywords
			#If there is more then one match, we will choose the one with more words in the keywords section
			#Note: This approach will not be able to deal with matches that are the highest amount of words and are equal in word count
			#Note cont: if this happens it will only be able to return the first of these matches

			for transaction_index in new_transactions_df.index:
				transaction_words = new_transactions_df.at[transaction_index, 'Trans']
				counterparty_matches = []
				for counterparty in counterparty_rows:
					counterparty_keywords = counterparty[1]
					if functions.keywordsmatch(transaction_words, counterparty_keywords):
						counterparty_matches.append((counterparty[0], counterparty_keywords, counterparty[2]))

				if len(counterparty_matches) > 0:
					most_keywords_match = (0, None)
					for match in counterparty_matches:
						if len(match[1].split()) > most_keywords_match[0]:
							most_keywords_match = (len(match[1].split()), match)
					new_transactions_df.at[transaction_index, 'Counterparty'] = most_keywords_match[1][0]
					new_transactions_df.at[transaction_index, 'Category'] = most_keywords_match[1][2]

			#We add data into the treeview, each row will get either an empty or found tag
			new_transactions_list = new_transactions_df.to_numpy().tolist()
			for row in new_transactions_list:
				if row[2] == 'N/A':
					new_transactions_treeview.insert('', 'end', values=row, tags=('empty',))
				else:
					new_transactions_treeview.insert('', 'end', values=row, tags=('found',))

		#Sets the tag to change a row's background color based on which tag they have
		new_transactions_treeview.tag_configure('empty', background='red')
		new_transactions_treeview.tag_configure('found', background='green')
		new_transactions_treeview.tag_configure('changed', background='yellow')

		

		'''Enter Counterparty Name Section'''

		#Here we have all the labels, entries, and buttons found below the Treeview in our Update CSV Window

		#Date
		date_label = Label(wrapper3, text="Date", font=('bold', 16))
		date_label.grid(row=0, column=0, sticky=W)

		global date_selection_text
		date_selection_text = StringVar()
		date_selection_label = Label(wrapper3, textvariable=date_selection_text)
		date_selection_label.grid(row=1, column=0, sticky=W)

		#Description
		description_label = Label(wrapper3, text="Description", font=('bold', 16))
		description_label.grid(row=2, column=0, sticky=W)

		global description_selection_text
		description_selection_text = StringVar()
		description_selection_label = Label(wrapper3, textvariable=description_selection_text)
		description_selection_label.grid(row=3, column=0, sticky=W)

		#Amount
		amount_label = Label(wrapper3, text="Amount", font=('bold', 16))
		amount_label.grid(row=4, column=0, sticky=W)

		global amount_selection_text
		amount_selection_text = StringVar()
		amount_selection_label = Label(wrapper3, textvariable=amount_selection_text)
		amount_selection_label.grid(row=5, column=0, sticky=W)

		#Counterparty
		counterparty_label = Label(wrapper4, text="Counterparty")
		counterparty_label.pack()

		global counterparty_selection_entry
		counterparty_selection_text = StringVar()
		counterparty_selection_entry = Entry(wrapper4, textvariable=counterparty_selection_text)
		counterparty_selection_entry.pack()

		#Keywords
		keywords_label = Label(wrapper4, text="Keywords")
		keywords_label.pack()

		global keywords_selection_entry
		keywords_selection_text = StringVar()
		keywords_selection_entry = Entry(wrapper4, textvariable=keywords_selection_text)
		keywords_selection_entry.pack()

		#Change Counterparty Button
		current_counterparty = counterparty_selection_entry.get()
		current_keywords = keywords_selection_entry.get()
		current_description = description_selection_text.get()
		change_counterparty_btn = Button(wrapper4, text="Change Counterparty", command=lambda: update_treeview(new_transactions_treeview, counterparty_selection_entry.get(),keywords_selection_entry.get(), description_selection_text.get()))
		change_counterparty_btn.pack()

		#Submit to database button
		submit_btn = Button(wrapper4, text="Submit to Database", command=lambda: functions.submit_treeview_to_db(new_transactions_treeview, database.submit_row_to_db, database.submit_counterparty_info, database.createtransactions, database.commitdb))
		submit_btn.pack()


	"""---------------------------------------------------------------------------------------------------------------------------------------------------------"""

	'''Main Window'''

	#Notebook & Tab/Frame creation
	notebook = ttk.Notebook(root)
	notebook.pack()

	main_frame = tk.Frame(notebook)
	notebook.add(main_frame, text="Main")

	#Upload Button
	upload_btn = Button(main_frame, text="Upload CSV", command=upload)
	upload_btn.grid(row=0, column=2, sticky=E, padx=20, pady=10)

	#Transaction List Frame
	wrapper1 = LabelFrame(main_frame, text="Transactions List")
	wrapper1.grid(row=1, column=0, padx=20, pady=10)


	global columns
	columns = ['Date', 'Description', 'Counterparty', 'Category', 'Amt']
	transactions_treeview = ttk.Treeview(wrapper1, columns=columns, show="headings")
	transactions_treeview.column("Date", width=80)
	transactions_treeview.column("Description", width=600)
	transactions_treeview.column("Counterparty", width=150)
	transactions_treeview.column("Category", width=150)
	transactions_treeview.column("Amt", width=80)

	for col in columns:
		transactions_treeview.heading(col, text=col)
	transactions_treeview.pack(side="left", fill="y")

	#Scrollbar that attachs to treeview
	scrollbar = Scrollbar(wrapper1, orient='vertical')
	scrollbar.configure(command=transactions_treeview.yview)
	scrollbar.pack(side="right", fill="y")
	transactions_treeview.config(yscrollcommand=scrollbar.set)


	#Frame for Transactions List buttons
	transbtn_frame = LabelFrame(main_frame, text="Search")
	transbtn_frame.grid(row=2, column=0, sticky=W, padx=20)

	#Labels for Transactions List
	date_label = Label(transbtn_frame, text="Date", font=('bold', 16))
	date_label.grid(row=0, column=0, sticky=E, padx=10, pady=10)

	year_label = Label(transbtn_frame, text="Year", font=('bold', 16))
	year_label.grid(row=1, column=0, sticky=E, padx=10, pady=10)

	counterparty_label = Label(transbtn_frame, text="Counterparty", font=('bold', 16))
	counterparty_label.grid(row=2, column=0, sticky=E, padx=10, pady=10)

	category_label = Label(transbtn_frame, text="Category", font=('bold', 16))
	category_label.grid(row=3, column=0, sticky=E, padx=10, pady=10)	

	#Combobox for Month Selection
	month_text = StringVar()
	month_text.set("January")
	month_combobox = ttk.Combobox(transbtn_frame, values=months, height=len(months), state="readonly", textvariable=month_text, width=10)
	month_combobox.grid(row=0, column=1)

	year_text = StringVar()
	year_text.set(datetime.today().year)
	year_entry = Entry(transbtn_frame, textvariable=year_text)
	year_entry.grid(row=1, column=1)

	#Entry for Counterparty and Category
	counterparty_search = StringVar()
	counterparty_search_entry = Entry(transbtn_frame, textvariable=counterparty_search)
	counterparty_search_entry.grid(row=2, column=1)

	category_search = StringVar()
	category_search_entry = Entry(transbtn_frame, textvariable=category_search)
	category_search_entry.grid(row=3, column=1)

	#Show Reset Default Button for Transactions list Treeview
	reset_default_btn = Button(main_frame, text="Reset Default", command=lambda: functions.insert_new_rows_into_treeview(database.defaultlist(), transactions_treeview))
	reset_default_btn.grid(row=2, column=0, sticky=E, padx=300, pady=10)

	#Show All Transactions Button
	show_all_btn = Button(main_frame, text="Show All Transactions", command=lambda: functions.insert_new_rows_into_treeview(database.alltransactions(), transactions_treeview))
	show_all_btn.grid(row=2, column=0, sticky=E, padx=50, pady=10)	

	#Search function
	def search_counterparty():
		month = month_combobox.get()
		year = year_entry.get()
		counterparty = counterparty_search_entry.get()

		transactions_treeview.delete(*transactions_treeview.get_children())

		if counterparty != '' or counterparty.isspace() == True:
			rows = database.search_counterparty_db(month, year, counterparty)
			for row in rows:
				transactions_treeview.insert('', 'end', values=row)
		else:
			rows = database.search_counterparty_db(month, year)
			for row in rows:
				transactions_treeview.insert('', 'end', values=row)

	def search_category():
		month = month_combobox.get()
		year = year_entry.get()
		category = category_search_entry.get()

		transactions_treeview.delete(*transactions_treeview.get_children())

		if category != '' or category.isspace() == True:
			rows = database.search_category_db(month, year, category)
			for row in rows:
				transactions_treeview.insert('', 'end', values=row)
		else:
			rows = database.search_category_db(month, year)
			for row in rows:
				transactions_treeview.insert('', 'end', values=row)

	#Search buttons for Counterparty and Category
	search_counterparty_btn = Button(transbtn_frame, text="Search Counterparty", command=search_counterparty)
	search_counterparty_btn.grid(row=2, column=2)

	search_category_btn = Button(transbtn_frame, text="Search Category", command=search_category)
	search_category_btn.grid(row=3, column=2)
			
	#Connection to database to return first 30 rows from database and insert into treeview
	#First time or no database detected then we will create a messagebox saying to click Upload CSV
	try:
		functions.insert_new_rows_into_treeview(database.defaultlist(), transactions_treeview)
	except database.sqlite3.OperationalError:
		tk.messagebox.showinfo(title="Welcome Box", message="Welcome to the Expense Tracker App. Please start by clicking the Upload CSV button")

	"""Functions Used"""
	def select_new_transaction(event, tree):
		try:
			global current_treeview_item_selected
			current_treeview_item_selected = tree.selection()[0]
			selected_item = tree.item(current_treeview_item_selected)['values']
			#print(new_transactions_treeview.item(current_treeview_item_selected)['text'])

			date_selection_text.set(selected_item[0])
			description_selection_text.set(selected_item[1])
			amount_selection_text.set(selected_item[4])
			counterparty_selection_entry.delete(0, END)
			counterparty_selection_entry.insert(END, selected_item[2])
			keywords_selection_entry.delete(0, END)
			keywords_selection_entry.insert(END, selected_item[5])

		except IndexError:
			pass

	#Function that is connected to the Change Counterparty button in New Window
	#This changes the counterparty value, once typed, for a given selected row
	#This will also change the counterparty of any row with the same description
	#If the change is different from 'N/A' (default counterparty) we change the background to yellow to show this was inputted
	def update_treeview(current_treeview, new_counterparty_name, new_keywords, selected_description):

		#if new_keywords.split() in selected_description:
		keywords_gen = (functions.keywordsmatch(new_keywords, keywords[0]) for keywords in database.getallkeywords())
		#keywords_exists_already = False #defining a variable to check if keywords are taken in database
		if True in keywords_gen: #if it does exist we change the value to True
			#keywords_exists_already = True
			tk.messagebox.showerror(title="Keyword Error", message="Keywords already exist")

		#This checks if the keywords
		elif new_keywords.isspace() or new_keywords == '':
			#keywords_exists_already = True
			tk.messagebox.showerror(title="Keyword Error", message="Please don't leave Keywords blank")

		elif database.checkifcounterpartyexists(new_counterparty_name) == 0 and new_counterparty_name != 'N/A': #use to have "and keywords_exists_already == False" at the end

			#changes the current selected row's counterparty to what was typed in
			#new_transactions_treeview.set(current_treeview_item_selected, column="Counterparty", value=new_counterparty_name)
			#new_transactions_treeview.set(current_treeview_item_selected, column="Keywords", value=new_keywords)
			keyword_in_descriptions = False

			for item in current_treeview.get_children():
				item_description = current_treeview.item(item)['values'][1]
				item_tag = current_treeview.item(item)['tags'][0]
				if functions.keywordsmatch(item_description, new_keywords) and item_tag != 'found': #checks if the description contains the keyword input only for rows that haven't already found a match from a database
						current_treeview.set(item, column="Counterparty", value=new_counterparty_name)
						current_treeview.set(item, column="Keywords", value=new_keywords)
						current_treeview.item(item,  tags='changed')
						keyword_in_descriptions = True
				print(current_treeview.item(item)['values'])
			if keyword_in_descriptions == False:
				print('Keywords not in description') #change this to error box	
			
		else:
			tk.messagebox.showerror(title="Change Counterparty Error", message="Something went wrong")
			#need to add error box here			

	"""------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------"""

	"""Counterparty Page"""

	#This will search for all transactions with N/A counterparties -- getallcounterparties_na()
	#It will take a user input for a counterparty name and keywords
	#It will need to check if the counterparty name and keywords are not already taken.
	#It will then need to check if there are any "N/A counterparty" transactions that that have keyword matches
	#If the last two lines are True, then we add information to counterparty table, change matched transaction to have this new counterparty, update the counterparty treeview in the tab
	def add_counterparty(database_function):
		pass

	#Choose selected counterparty in treeview
	#Will bring up a messagebox if they are sure they want to delete this counterparty, will show name of counterparty, yes button, and cancel button
	#Also say this will change all transactions with the counterparty to have "N/A" in counterparty column.
	#If they click yes then change all transactions with the selected counterparty to "N/A" in the counterparty column
	#Then remove the selected counterparty row from the counterparty table.
	#Update the counterparty and category treeview to reflect this change 
	#show a messagebox that says the counterparty has been deleleted and all the transactions with the counterparty have been updated 
	def delete_counterparty(tree):
		delete_counter = tk.messagebox.askyesno(title="Delete Counterparty?", 
												message="Do you really want to delete this counterparty? Deleting will change all the transactions with this counterparty to 'N/A'.")
		
		if selected_counterparty_name == "N/A":
			tk.messagebox.showerror(title="Error", message="That row is not allowed")

		elif delete_counter:
			try:
				database.all_counterparties_trans(selected_counterparty_name)
				tk.messagebox.showinfo('Deleted Counterparty', 'You deleted ' + str(selected_counterparty_name))
			except:
				tk.messagebox.showerror(title="Error", message="Please select a row from the counterparty table")


	#Counterparty Frame
	counterparty_frame = tk.Frame(notebook)
	notebook.add(counterparty_frame, text="Counterparty")

	#Wrapper for Treeview
	counterparty_wrapper1 = LabelFrame(counterparty_frame, text="Counterparies")
	counterparty_wrapper1.pack()

	counterparty_wrapper2 = LabelFrame(counterparty_frame, text="Update Counterparties")
	counterparty_wrapper2.pack()

	#Counterparty Buttons
	add_counterparty_btn = Button(counterparty_wrapper2, text="Add Counterparty", command= lambda: functions.add_counterparty(database.getalltransactions_NA(), database.checkifcounterpartyexists, database.getallkeywords(), database.updatetransaction, database.submit_counterparty_info_from_btn, counterparty_name_entry.get(), keywords_entry.get()))
	delete_counterparty_btn = Button(counterparty_wrapper2, text="Delete Counterparty", command= lambda: delete_counterparty(counterparty_treeview))
	refresh_btn = Button(counterparty_wrapper2, text='Refresh', command= lambda: functions.insert_new_rows_into_treeview(database.getallcounterparties(), counterparty_treeview))

	add_counterparty_btn.grid(row=2, column=1, sticky=W, padx=40)
	delete_counterparty_btn.grid(row=3, column=1, sticky=W, padx=40)
	refresh_btn.grid(row=4, column=1, sticky=W, padx=40)

	#Counterparty Treeview setup
	counterparty_columns = ["Counterparty", "Keywords", "Category"]
	counterparty_treeview = ttk.Treeview(counterparty_wrapper1, columns=counterparty_columns, show="headings")

	counterparty_treeview.column("Counterparty", width=150)
	counterparty_treeview.column("Keywords", width=150)
	counterparty_treeview.column("Category", width=150)

	for col in counterparty_columns:
		counterparty_treeview.heading(col, text=col)

	for row in database.getallcounterparties(): 
		counterparty_treeview.insert('', 'end', values=row)

	counterparty_treeview.grid(row=0, column=0, padx=10, pady=5)

	name_text = StringVar()
	counterparty_name_label = Label(counterparty_wrapper2, text="Name", font=('bold', 16))
	counterparty_name_label.grid(row=1, column=0, padx=40)
	counterparty_name_entry = Entry(counterparty_wrapper2, text=name_text)
	counterparty_name_entry.grid(row=2, column=0, padx=40, pady=6)

	keywords_text = StringVar()
	keywords_label = Label(counterparty_wrapper2, text="Keywords", font=('bold', 16))
	keywords_label.grid(row=3, column=0, padx=40)
	keywords_entry = Entry(counterparty_wrapper2, text=keywords_text)
	keywords_entry.grid(row=4, column=0, padx=40, pady=6)

	counterparty_treeview.bind('<<TreeviewSelect>>', lambda event: selected_counterparty(event, counterparty_treeview))

	def selected_counterparty(event, tree):

		current_selection = tree.selection()[0]
		selected_item = tree.item(current_selection)['values']
		global selected_counterparty_name
		selected_counterparty_name = selected_item[0]

	"""------------------------------------------------------------------------------------------------------------------------------------------------"""

	"""Category Page"""

	#Functions for categories

	def delete_category():

		delete_category = tk.messagebox.askyesno(title="Delete Category?", 
												message="Do you really want to delete this category? Deleting will change all the transactions/counterparties with this category to 'N/A'.")
		
		if selected_category_name == "None" or selected_category_name == "N/A":
			tk.messagebox.showerror(title="Error", message="That row is not allowed")

		elif delete_category:
			try:
				database.delete_a_category(selected_category_name)
				tk.messagebox.showinfo('Deleted Category', 'You deleted ' + str(selected_category_name))
			except:
				tk.messagebox.showerror(title="Error", message="Please select a row from the category table")


	category_frame = tk.Frame(notebook)
	notebook.add(category_frame, text="Category")

	#Wrappers for Widgets
	category_wrapper1 = LabelFrame(category_frame, text="Categories")
	category_wrapper1.pack()

	category_wrapper2 = LabelFrame(category_frame, text="Update Categories")
	category_wrapper2.pack()

	#Category Treeview setup
	category_columns = ["Category", "Counterparties"]
	category_treeview = ttk.Treeview(category_wrapper1, columns=category_columns, show="headings")

	category_treeview.column("Category", width=200)
	category_treeview.column("Counterparties", width=700)

	for col in category_columns:
		category_treeview.heading(col, text=col)

	for category in database.getallcategories():
		current_category = category[0]
		counterparties_list = database.get_counterparties_for_category(current_category)
		treeview_row = []
		separator = ', '
		current_counterparties = separator.join(counterparties[0] for counterparties in counterparties_list)
		treeview_row.append(current_category)
		treeview_row.append(current_counterparties)
		category_treeview.insert('', 'end', values=treeview_row)

	category_treeview.pack()


	#Category Buttons
	add_category_btn = Button(category_wrapper2, text="Add Category", command= lambda: functions.add_category(category_entry.get(), counterparty_entry.get(), database.checkifcategoryexists, database.checkifcounterpartyexists, database.getonecounterparty, database.updatecategory))
	del_category_btn = Button(category_wrapper2, text="Delete Category", command=delete_category)

	add_counterparty_to_category_btn = Button(category_wrapper2, text="Add Counterparty to Category", command= lambda: functions.add_counterparty_to_category(selected_category_name, counterparty_entry.get(), database.checkifcounterpartyexists, database.checkifcategoryexists, database.getonecounterparty, database.updatecategory))
	del_counterparty_to_category_btn = Button(category_wrapper2, text="Delete Counterparty from Category", command= lambda: functions.delete_counterparty_from_category(selected_category_name, counterparty_entry.get(), database.checkifcounterpartyexists, database.getonecounterparty, database.updatecategory))

	category_refresh_btn = Button(category_wrapper2, text="Refresh", command= lambda: functions.category_refresh(category_treeview, database.getallcategories(), database.get_counterparties_for_category))


	add_category_btn.pack()
	del_category_btn.pack()

	add_counterparty_to_category_btn.pack()
	del_counterparty_to_category_btn.pack()

	category_refresh_btn.pack()

	#Entry for Categories
	category_text = StringVar()
	add_category_label = Label(category_wrapper2, text="Category Name", font=('bold', 16))
	add_category_label.pack()
	category_entry = Entry(category_wrapper2, text=category_text)
	category_entry.pack()

	counterparty_text = StringVar()
	add_counterparty_label = Label(category_wrapper2, text="Counterparty Name", font=('bold', 16))
	add_counterparty_label.pack()
	counterparty_entry = Entry(category_wrapper2, text=counterparty_text)
	counterparty_entry.pack()

	category_treeview.bind('<<TreeviewSelect>>', lambda event: selected_category(event, category_treeview))


	def selected_category(event, tree):

		current_selection = tree.selection()[0]
		selected_item = tree.item(current_selection)['values']
		global selected_category_name
		selected_category_name = selected_item[0]

	"""------------------------------------------------------------------------------------------------------------------------------------------------"""

	"""Graph Window"""

	#Graphs Frame
	graphs_frame = tk.Frame(notebook)
	notebook.add(graphs_frame, text="Graphs")

	pie_graph_counterparty = Button(graphs_frame, text="All Pie Chart Counterparties", command=lambda: functions.pie_graph(database.get_all_counterparty_percentages(), "All Counterparties by % of Total Amount"))
	pie_graph_counterparty.pack()

	pie_graph_category = Button(graphs_frame, text="All Pie Chart Categories", command=lambda: functions.pie_graph(database.get_all_category_percentages(), "All Categories by % of Total Amount"))
	pie_graph_category.pack()

	bar_graph_counterparty = Button(graphs_frame, text="All Counterparties", command=lambda: functions.bar_graph(database.get_all_counterparty_amounts(), "All Counterparties"))
	bar_graph_counterparty.pack()

	bar_graph_category = Button(graphs_frame, text="All Categories", command=lambda: functions.bar_graph(database.get_all_category_amounts(), "All Categories"))
	bar_graph_category.pack()

	root.mainloop()

		

