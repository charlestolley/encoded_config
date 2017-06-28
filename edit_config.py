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
	if not outfile in ALLOWED_FILES:
		print "Invalid attempt to edit '" + outfile + "'"
		print "This script may only edit the following files:"
		print ALLOWED_FILES
		return
	try:
		contents = get_contents(infile)
	except IOError:
		print "Could not open '" + infile + "' for reading\n"
		return
	header = contents.pop('header')
	for var_name in contents.keys():
		if len(contents[var_name]) > 1:
			print "Multiple declarations found for " + var_name
		for instance in contents[var_name]:
			instance['value'] = '"' + base64.b64encode(instance['value']) + '"'
	write_to_file(outfile, contents, header)

def get_contents(filename):
	# IOError not caught here
	file_in = open(filename, 'r')

	line_buffer = ''
	begin = False
	contents = {'header':DEFAULT_HEADER}
	for line in file_in.readlines():
		if not begin and re.search(r'^\s*#', line):
			line_buffer += line
			header_end = re.search(r'^#{2,}$', line)
			if header_end:
				contents['header'] = line_buffer.strip()
				line_buffer = ''
				begin = True
		else:
			declaration = re.search(r'^\s*([A-Z_][A-Z0-9_]*)\s*=\s*(.*)\s*$', line)
			if declaration:
				var = declaration.group(1)
				value = declaration.group(2)
				if not var in contents:
					contents[var] = []
				line_buffer = line_buffer.strip()
				if line_buffer:
					line_buffer = '\n' + line_buffer + '\n'
				contents[var].append({"comments":line_buffer, "value":value})
				line_buffer = ''
			else:
				if re.search(r'^\s*#', line):
					line_buffer += line
	file_in.close()
	return contents

# returns a list of all values assigned
# to a given variable name (decoded)
def get_values(filename, var_name):
	try:
		infile = open(filename, 'r')
	except TypeError as e:
		print "Could not open '" + filename + "': " + e.message
		raise
	encoded_vals = []
	decoded_vals = []
	for line in infile.readlines():
		match = re.search(r'^\s*([A-Z_][A-Z0-9_]*)\s*=\s*(.*)\s*$', line)
		if match and match.group(1) == var_name:
			encoded_vals.append(match.group(2))
	infile.close()
	for val in encoded_vals:
		if not re.search(r'^(")[a-zA-Z0-9+/]+={0,2}(\1)$', val):
			sys.stderr.write("Unencoded value found in config: " + val + '\n')
			decoded_vals.append(val)
		else:
			try:
				decoded_vals.append(base64.b64decode(val))
			except TypeError as e:
				sys.stderr.write("Error decoding value: " + str(e.message) + '\n')
				decoded_vals.append(val)
	return decoded_vals

def new(filename):
	if isfile(filename):
		print "Cannot create " + filename + " because it already exists"
		return
	with open(filename, 'w') as newfile:
		pass
	ALLOWED_FILES.append(abspath(filename))
	header = get_contents(filename)['header']
	write_to_file(filename, {}, header)
	print "File successfully created!"
	print "Add " + filename + " to ALLOWED_FILES in edit_config.py in order to edit it"

def remove(filename, var_name):
	filename = abspath(filename)
	if not filename in ALLOWED_FILES:
		print "This script may only edit the following files:"
		print ALLOWED_FILES
		return
	try:
		contents = get_contents(filename)
	except IOError:
		print "Could not open '" + infile + "' for reading\n"
		return
	header = contents.pop('header')
	if var_name in contents:
		contents.pop(var_name)
		write_to_file(filename, contents, header)
	else:
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

def write_to_file(filename, contents, header=''):
	file_out = open(filename, 'w')
	file_out.write(header + '\n')
	first = True
	for key in sorted(contents.keys()):
		for var in contents[key]:
			if var['comments']:
				file_out.write(var['comments'])
			elif first:
				file_out.write('\n')
			file_out.write(key + '=' + var['value'] + '\n')
			first = False
	file_out.close()

### Execution begins here ###
COMMANDS = {	"encode":	{	"func":		encode, 
								"usage":	"<in_file> [out_file]\n" +
											"Accepts a config file of the appropriate format with\n" +
											"contents in plain text and base64 encodes the values"},
				"new":		{	"func":		new,
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
