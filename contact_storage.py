#!/usr/bin/env python3
# -*- coding: utf8 -*-

import csv

class contactlist:
	_list = []
	
	# Status:
	# 410 = User has closed it's Account
	# 200 = User has been found
	def add(self, userinfo, days_since_last_post, status):
		if('name' not in userinfo.data): # make sure there is a value to the "name"-key
			userinfo.data['name'] = "(none)"
		self._list.append( (userinfo, days_since_last_post, status) )
	
	# Sorts the list by number of posts, descending
	def get_sorted(self):
		return sorted(self._list, key=lambda c: c[1], reverse=True)
	
	def save_as_csv(self, filename):
		with open(filename, 'w', newline='') as csvfile:
			writefile = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
			
			for row in self._list:
				# (handle, name), days_since_last_post, status
				writefile.writerow([ row[0]['handle'], row[0]['name'], row[1], row[2] ])
		
		csvfile.close()
	
	def load_from_csv(self, filename):
		with open(filename, 'w', newline='') as csvfile:
			self._list = [] # We load a fresh list
			readfile = csv.reader(csvfile, delimiter=',', quotechar='"')
			
			for row in readfile:
				# (handle, name), days_since_last_post, status
				self._list.append( ({'handle': row[0], 'name': row[1]}, row[2], row[3]) )
		
		csvfile.close()
