import base64
from os.path import abspath, isfile
import re
import sys

import config_utils

if __name__ != '__main__':
	sys.exit()

ALLOWED_FILES = []

DEFAULT_HEADER = """\
##################### Header #####################
# Anything contained in this header will be pre-
# served by edit_config.py as long as every line
# begins with a single '#' symbol. A line
# beginning with 2 or more '#' characters and
# containing nothing else will be interpreted as
# the end of the header.
# 
# Comments included anywhere else in the file are
# associated with the variable that immediately
# follows, and may be reformatted to reflect that
# association. If a variable is removed, its
# associated comments will also be removed.
##################################################\
"""

def encode(infile, outfile=None):
	infile = abspath(infile)
	outfile = abspath(outfile) if outfile else infile
	if isfile(outfile) and not outfile in ALLOWED_FILES:
		print "Invalid attempt to edit '" + outfile + "'"
		print "This script may only edit the following files:"
		print ALLOWED_FILES
		return
	config_utils.encode(infile, outfile)

def remove(filename, var_name):
	filename = abspath(filename)
	if not filename in ALLOWED_FILES:
		print "This script may only edit the following files:"
		print ALLOWED_FILES
		return
	if not config_utils.remove(filename, var_name):
		print "Variable " + var_name + " does not exist"

def show(filename, var_name):
	values = config_utils.get_values(filename, var_name)
	if not values:
		print "Variable '" + var_name + "' not found"
	elif len(values) > 1:
		print "Multiple values found for '" + var_name + "'"
	for val in values:
		print var_name + "=" + val

def show_all(filename):
	contents = config_utils.get_contents(filename)
	for var_name in sorted(contents['vars']):
		print var_name

def usage(command=None):
	print "Usage: " + sys.argv[0],
	if command:
		print command + " " + COMMANDS[command]["usage"]
	else:
		print "<command> [args]\n"
		print "Available commands are:"
		for cmd in sorted(COMMANDS.keys()):
			print cmd
		print "You may enter a command without args to see its usage\n"

### Execution begins here ###
COMMANDS = {	"encode":	{	"func":		encode, 
								"usage":	"<in_file> [out_file]\n" +
											"Accepts a config file of the appropriate format with\n" +
											"contents in plain text and base64 encodes the values"},
				"new":		{	"func":		config_utils.new,
								"usage":	"<file>\n" +
											"Creates a new empty config file"},
				"remove":	{	"func":		remove,
								"usage":	"<file> <var_name>\n" +
											"Deletes the variable <var_name> from <file>"},
				"set":		{	"func":		config_utils.set_value, 
								"usage":	"<file> <var_name> <value>\n" +
											"base64 encodes the given value and writes it to var_name"},
				"show":		{	"func":		show,
								"usage": 	"<file> <var_name>\n" + 
											"Shows the decoded value of the variable <var_name>"},
				"show-all":	{	"func":		show_all,
								"usage":	"<file>\n" +
											"Lists the names of all variables in <file> (no values)"}}

if len(sys.argv) == 1:
	usage()
	sys.exit()

if not sys.argv[1] in COMMANDS:
	usage()
	sys.exit()

try:
	COMMANDS[sys.argv[1]]["func"](*sys.argv[2:])
except TypeError as e:
	usage(sys.argv[1])
	sys.exit()
