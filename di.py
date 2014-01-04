#!/usr/bin/env python3
# -*- coding: utf8 -*-

import argparse
import configparser
import dateutil.parser
import datetime
import diaspy
import contact_storage
import json #debug

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


### Reads the list of contacts from a diaspora-Account and saved them to a csv-file
def examine_user_list():
	# Connect
	con = diaspy.connection.Connection(config['Diaspora']['pod'], config['Diaspora']['username'], config['Diaspora']['password'])
	con.login()

	# Storage for our findings
	contact_list = contact_storage.contactlist()

	# Get all contacts
	contacts = diaspy.people.Contacts(con)
	result = contacts.get()
	print("Number of Contacts: {0}".format(len(result)))

	total_num = len(result)
	current_num = 0

	for current_contact in result[7:15]:
		current_num += 1
		print("{0} / {1}".format(current_num, total_num), end="")
		
		try:
			current_contact.fetchhandle()
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

		if(last_post_date is not None):
			days_since_last_post = (current_datetime - last_post_date).days
		else:
			days_since_last_post = 10000000 # 10 Millionen ... da kommen wir nie hin.

		contact_list.add(current_contact, days_since_last_post, 200)
		print("{0} [ {1} ] --> Days since last post: {2}".format(current_contact['name'], current_contact['handle'], days_since_last_post))

	contact_list.save_as_csv("userlist.csv")
	print("Userlist saved to userlist.csv")



### Start the Tool
args = parser.parse_args()

if(args.action == 'select'):
	print("hallo")

print(args)
exit()




#print("Days since last post: {0}".format(days_since_last_post))
#	print("No public posts.")

#print(json.dumps(result[0].stream[0]._data, sort_keys=True, indent=2))



# Add Aspect
#diaspy.streams.Aspects(test_connection).add(testconf.test_aspect_name_fake)
#testconf.test_aspect_id = diaspy.streams.Aspects(test_connection).add(testconf.test_aspect_name).id

# Remove Aspect
#aspects = diaspy.streams.Aspects(test_connection)
#for i in test_connection.getUserData()['aspects']:
#	if i['name'] == testconf.test_aspect_name:
#		print(i['id'], end=' ')
#		aspects.remove(id=i['id'])
#		break
             
