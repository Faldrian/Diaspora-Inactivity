#!/usr/bin/env python3
# -*- coding: utf8 -*-

import configparser
import diaspy

# Read Login-Settings
config = configparser.ConfigParser()
config.read('config.ini')

# Connect

con = diaspy.connection.Connection(config['Diaspora']['pod'], config['Diaspora']['username'], config['Diaspora']['password'])
con.login()

