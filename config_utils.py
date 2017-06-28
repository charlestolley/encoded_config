import base64
from os.path import isfile
import re

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

header_regex = re.compile(r'(?i)^#+\s*header\s*#+$')
header_end_regex = re.compile(r'^#{2,}$')
comment_regex = re.compile(r'^\s*(#.*?)\s*$')
declaration_regex = re.compile(r'^\s*([A-Z][A-Z0-9_]*)\s*=\s*"(.*)"\s*$')
var_name_regex = re.compile(r'^[A-Z_][A-Z0-9_]*$')

def encode(infile, outfile=None):
	if not outfile:
		outfile = infile
	contents = get_contents(infile)
	for var in contents['vars']:
		for occurrence in contents['vars'][var]:
			occurrence['value'] = base64.b64encode(occurrence['value'])
	write_to_file(outfile, contents)

# Returns a dictionary of the following format
#	{
#		'header': <string>
#		'vars': {
#			<var_name>: [
#				{
#					'comments': <string>
#					'value': <string>
#				}
#				{
#					'comments': <string>
#					'value': <string>
#				}
#				...
#			]
#			<var_name>: [
#				{
#					'comments': <string>
#					'value': <string>
#				}
#				{
#					'comments': <string>
#					'value': <string>
#				}
#				...
#			]
#			...
#		}
#	}
# It thereby accommodates the case where there are 
# multiple copies of a variable with a single name;
# even though such a case is not supported, it isn't
# up to the get_contents function to discard information.
def get_contents(filename):
	contents = {
		'header': '',
		'vars': {}
	}

	try:
		file_in = open(filename, 'r')
	except IOError:
		return contents

	first_line = file_in.readline()
	if re.search(header_regex, first_line):
		header = first_line
		while True:
			line = re.search(comment_regex, file_in.readline())
			if line:
				line = line.group(1)
				header += line + '\n'
				if re.search(header_end_regex, line):
					break
		# still includes trailing newline, but that's actually okay
		contents['header'] = header
	else:
		# need to get the first line back
		file_in.close()
		file_in = open(filename, 'r')

	line_buffer = ''
	for line in file_in.readlines():
		declaration = re.search(declaration_regex, line)
		if declaration:
			var = declaration.group(1)
			value = declaration.group(2)
			if not var in contents['vars']:
				contents['vars'][var] = []
			contents['vars'][var].append({'comments':line_buffer.strip(), 'value':value})
			line_buffer = ''
		elif re.search(comment_regex, line):
			line_buffer += line

	file_in.close()
	return contents

# Unlike get_values, this function returns specifically
# the first occurrence of the value in the config file.
# This only matters if your config has duplicate names (which it shouldn't)
def get_raw_value(filename, var_name):
	if not re.search(var_name_regex, var_name):
		raise ValueError("var_name must match '^[A-Z_][A-Z0-9_]*$'")
	with open(filename, 'r') as file_in:
		value = None
		try:
			while value is None:
				declaration = re.search(declaration_regex, file_in.next())
				if declaration and declaration.group(1) == var_name:
					value = declaration.group(2)
		except StopIteration:
			pass
		return value

# returns a list of all values assigned
# to a given variable name
def get_raw_values(filename, var_name):
	contents = get_contents(filename)
	if var_name in contents['vars']:
		return [occurrence['value'] for occurrence in contents['vars'][var_name]]

def get_value(filename, var_name):
	return base64.b64decode(get_raw_value(filename, var_name))

def get_values(filename, var_name):
	return [base64.b64decode(value) for value in get_raw_values(filename, var_name)]

# creates a new config file with default header
# throws ValueError if the file already exists
def new(filename):
	if isfile(filename):
		raise ValueError("Cannot create {} because it already exists".format(filename))
	contents = get_contents(filename)
	contents['header'] = DEFAULT_HEADER
	write_to_file(filename, contents)

def remove(filename, var_name):
	contents = get_contents(filename)
	if var_name in contents['vars']:
		contents['vars'].pop(var_name)
		write_to_file(filename, contents)
		return True
	else:
		return False

# Overwrites previous value(s)
def set_raw_value(filename, var_name, value):
	if not re.search(var_name_regex, var_name):
		raise ValueError("var_name must match '^[A-Z_][A-Z0-9_]*$'")
	contents = get_contents(filename)
	# preserve the comments for a variable
	comments = []
	if var_name in contents['vars']:
		for occurrence in contents['vars'][var_name]:
			if occurrence['comments']:
				comments.append(occurrence['comments'])
	contents['vars'][var_name] = [
		{
			'comments': '\n'.join(comments),
			'value': value
		}
	]
	write_to_file(filename, contents)

def set_value(filename, var_name, value):
	set_raw_value(filename, var_name, base64.b64encode(value))

# see get_contents for the formatting of <contents>
def write_to_file(filename, contents):
	with open(filename, 'w') as file_out:
		file_out.write(contents['header'])
		var_names = sorted(contents['vars'])
		if var_names and not contents['vars'][var_names[0]][0]['comments']:
			file_out.write('\n')
		for var in var_names:
			for occurrence in contents['vars'][var]:
				comments = occurrence['comments']
				value = occurrence['value']
				if comments:
					file_out.write('\n')
					file_out.write(comments)
					file_out.write('\n')
				file_out.write('{0}="{1}"'.format(var, value))
				file_out.write('\n')
