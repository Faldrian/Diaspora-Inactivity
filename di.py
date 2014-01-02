#!/usr/bin/env python3
# -*- coding: utf8 -*-

import configparser
import dateutil.parser
import datetime
import diaspy
import json #debug

# Current timezone-aware datetime-stamp for later use
current_datetime = datetime.datetime.utcnow().replace(tzinfo=dateutil.tz.tzutc())


# Read Login-Settings
config = configparser.ConfigParser()
config.read('config.ini')

# Connect
con = diaspy.connection.Connection(config['Diaspora']['pod'], config['Diaspora']['username'], config['Diaspora']['password'])
con.login()


contact_list = []

# Get all contacts
contacts = diaspy.people.Contacts(con)
result = contacts.get()
print("Number of Contacts: {0}".format(len(result)))

total_num = len(result)
current_num = 0

for current_contact in result:
	current_contact.fetchhandle()

	# Is there any post?
	if(len(current_contact.stream) > 0):
		# Get date of last post
		last_post_date = dateutil.parser.parse(current_contact.stream[0]['created_at'])

	if(last_post_date is not None):
		days_since_last_post = (current_datetime - last_post_date).days
	else:
		days_since_last_post = 10000000 # 10 Millionen ... da kommen wir nie hin.

	contact_list.append( (current_contact, days_since_last_post) )
	
	current_num += 1
	print("{0} / {1}".format(current_num, total_num))

sorted_contact_list = sorted(contact_list, key=lambda c: c[1], reverse=True)
for contact in sorted_contact_list:
	print("{0} [ {1} ] --> Days since last post: {2}".format(contact[0]['name'], contact[0]['handle'], contact[1]))


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
             
