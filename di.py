#!/usr/bin/env python3
# -*- coding: utf8 -*-

import argparse
import configparser
import dateutil.parser
import datetime
import diaspy
import contact_storage
import json #debug
import requests

parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
	description="""Manage your Diaspora-Contact-List: Clean old Contacts.
1. "list"-action:
   Let the script examine your contact-list
   and create a CSV-File containing information.

2. "select"-action:
   Select contacts from the CSV-File.
   By default no contact is selected, use the optional parameters
   to select contacts.
   This writes the selection-file.

3. "notify"-action:
   Let this Tool write your contacts a message,
   asking if they are still on Diaspora.
   All contacts in the selection-file will be asked.

4. "remove"-action:
   The Tool will remove all contacts in the selection-file
   from your Diaspora-Contact-List.""")
parser.add_argument('action', choices=['list', 'select', 'notify', 'remove'], help='Action to execute. See list above.')
parser.add_argument('--min_days', type=int, help='Select Accounts with MIN_DAYS days that passed since last public post.')
parser.add_argument('--account_closed', action="store_const", const=True, default=False, help='Select closed Diaspora-Accounts.')


# Current timezone-aware datetime-stamp for later use
current_datetime = datetime.datetime.utcnow().replace(tzinfo=dateutil.tz.tzutc())

# Read Login-Settings
config = configparser.ConfigParser()
config.read('config.ini')

# Filenames
file_list = "userlist.csv"
file_select = "userselect.csv"


### Reads the list of contacts from a diaspora-Account and saved them to a csv-file
def examine_user_list(outputfile):
	# Connect
	con = diaspy.connection.Connection(config['Diaspora']['pod'], config['Diaspora']['username'], config['Diaspora']['password'])
	con.set_verify_SSL(False)
	con.login()

	# Storage for our findings
	contact_list = contact_storage.contactlist()

	# Get all contacts
	contacts = diaspy.people.Contacts(con)
	result = contacts.get()
	print("Number of Contacts: {0}".format(len(result)))
	
	total_num = len(result)
	current_num = 0

	for current_contact in result:
		current_num += 1
		print("{0} / {1}".format(current_num, total_num), end="")
		
		try:
			current_contact.fetchhandle()
		except requests.exceptions.SSLError as err:
			print(" SSL-Error fetching User ({0}). Skipping.".format(current_contact['handle']))
			continue
		except requests.exceptions.ConnectionError as err:
			print(" Connection-Error fetching User ({0}). Skipping.".format(current_contact['handle']))
			continue
		except Exception as err:
			if err.args[0].endswith("410"):
				# This contact has closed it's diaspora-account.
				contact_list.add(current_contact, 10000000, 410) # Store that Error
				print(" User closed Account ({0}).".format(current_contact['handle']))
				continue # Skip to next contact
			else:
				pass # We want to know what else could go wrong
		
		# Is there any post?
		if(len(current_contact.stream) > 0):
			# Get date of last post
			last_post_date = dateutil.parser.parse(current_contact.stream[0]['created_at'])
			days_since_last_post = (current_datetime - last_post_date).days
		else:
			days_since_last_post = 10000000 # 10 Millionen ... da kommen wir nie hin.
		
		contact_list.add(current_contact, days_since_last_post, 200)
		print(" {0} [ {1} ] --> Days since last post: {2}".format(current_contact['name'], current_contact['handle'], days_since_last_post))

	contact_list.save_as_csv(outputfile)
	print("Userlist saved to " + outputfile)


### Filters the userlist and selects users
def select_users(inputfile, outputfile, account_closed, min_days):
	# Get users from storage
	contact_list = contact_storage.contactlist()
	contact_list.load_from_csv(inputfile)
	
	# Open selected list
	select_list = contact_storage.contactlist()
	
	usercounter = 0
	for cur_user in contact_list.get_list():
		# Account is closed?
		if account_closed and int(cur_user[2]) == 410:
			select_list.add_from_list(cur_user)
			usercounter += 1
			continue
		
		# Account is too old?
		if min_days is not None and int(cur_user[1]) >= min_days:
			select_list.add_from_list(cur_user)
			usercounter += 1
			continue
	
	select_list.save_as_csv(outputfile)
	print("Selection saved to " + outputfile + ", selected " + str(usercounter) + " Accounts.")

def notify_users(inputfile):
	print("Tschuldigung.")
	# Show a List of users we want to notify and request any response from.


def remove_users(inputfile):
	# Connect
	con = diaspy.connection.Connection(config['Diaspora']['pod'], config['Diaspora']['username'], config['Diaspora']['password'])
	con.set_verify_SSL(False)
	con.login()
	
	# Load selected users
	print("Loading Selection-List")
	remove_list = contact_storage.contactlist()
	remove_list.load_from_csv(inputfile)
	
	# Show a List of users we want to remove and request "YES"
	print("The following Diaspora-Accounts will be removed from your contacts:\n")
	for remove_list_user in remove_list.get_list():
		print("{0:40} ({1})".format(remove_list_user[0]['name'], remove_list_user[0]['handle']))
	
	confirmation = input("\nType 'YES' to continue: ")
	if(confirmation != "YES"):
		print("Aborted.")
		return
	
	# Build a list only containing handles of users to remove
	remove_list_handles = []
	for remove_list_user in remove_list.get_list():
		remove_list_handles.append(remove_list_user[0]['handle'])
	
	# Get all Contacts and create a guid --> handle dictionary
	print("Build cache for user-guids")
	guid_to_handle = {}
	contacts = diaspy.people.Contacts(con)
	for contact in contacts.get():
		guid_to_handle[contact.data['guid']] = contact.data['handle']
	
	
	# Get all Aspects of this Account
	print("Get all Aspects of Diaspora-Account")
	userdata = con.getUserData()
	aspects = userdata['aspects']
	
	# Iterate all Aspects, if there is a guid that translates to a handle that is on the remove_list, remove the user
	for current_aspect in aspects:
		aspect_obj = diaspy.models.Aspect(con, current_aspect['id'])
		print(">>> Working on Aspect {0}".format(aspect_obj.name))
		for aspect_user_guid in aspect_obj.getUsers():
			# Check if this user is really one of my users ... there is a bug in Diaspora, "getUsers" shows WAY to many users!
			if aspect_user_guid not in guid_to_handle:
				continue
			aspect_user_handle = guid_to_handle[aspect_user_guid]
			
			if aspect_user_handle in remove_list_handles:
				
				aspect_user_id = None
				try:
					aspect_user_obj = diaspy.people.User(con, guid=aspect_user_guid, handle=aspect_user_handle, fetch='data')
					aspect_user_id = aspect_user_obj.data['id']
				except diaspy.errors.UserError as err:
					print(err)
					print("--> Retrying using another Method.")
					# Retry fetching "posts" instead
					try:
						aspect_user_obj = diaspy.people.User(con, guid=aspect_user_guid, handle=aspect_user_handle, fetch='posts')
						aspect_user_id = aspect_user_obj.data['id']
					except Exception as err:
						print(err)
						print(":-( :-( :-( Giving up. Skipping to the next.")
						continue
				
				print("Remove {0} from Aspect {1}, internal ID={2}".format(aspect_user_handle, aspect_obj.name, aspect_user_id))
				#aspect_obj.removeUser(aspect_user_id)
	
	


### Start the Tool
args = parser.parse_args()

if args.action == 'list':
	examine_user_list(file_list)

if args.action == 'select':
	select_users(file_list, file_select, args.account_closed, args.min_days)

if args.action == 'notify':
	notify_users(file_select)

if args.action == 'remove':
	remove_users(file_select)

