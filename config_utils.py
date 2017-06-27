import base64
from pprint import pprint
import re

header_regex = re.compile(r'(?i)^#+\s*header\s*#+$')
header_end_regex = re.compile(r'^#{2,}$')
comment_regex = re.compile(r'^\s*(#.*?)\s*$')
declaration_regex = re.compile(r'^\s*([A-Z][A-Z0-9_]*)\s*=\s*"([a-zA-Z0-9+\=]*)"\s*$')
var_name_regex = re.compile(r'^[A-Z][A-Z0-9_]*$')

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
# up to the get_contents function to discard information
def get_contents(filename):
	contents = {
		'header': '',
		'vars': {}
	}

	file_in = open(filename, 'r')

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
			value = base64.b64decode(declaration.group(2))
			if not var in contents['vars']:
				contents['vars'][var] = []
			contents['vars'][var].append({'comments':line_buffer.strip(), 'value':value})
			line_buffer = ''
		elif re.search(comment_regex, line):
			line_buffer += line

	file_in.close()
	return contents

# Unlike get_contents, this function returns specifically
# the first occurrence of the value in the config file.
# This only matters if your config has duplicate names (which it shouldn't)
def get_value(filename, var_name):
	if not re.search(var_name_regex, var_name):
		raise ValueError("var_name must match '^[A-Z][A-Z0-9_]*$'")
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

# Overwrites previous value(s)
def set_value(filename, var_name, value):
	if not re.search(var_name_regex, var_name):
		raise ValueError("var_name must match '^[A-Z][A-Z0-9_]*$'")
	contents = get_contents(filename)
	# preserve the comments for a variable
	comments = []
	if var_name in contents['vars']:
		for occurrence in contents['vars'][var_name]:
			comments.append(occurrence['comments'])
	contents['vars'][var_name] = [
		{
			'comments': '\n'.join(comments),
			'value': value
		}
	]
	write_to_file(filename, contents)

# see get_contents for the formatting of <contents>
def write_to_file(filename, contents):
	with open(filename, 'w') as file_out:
		file_out.write(contents['header'])
		var_names = sorted(contents['vars'])
		if var_names and not contents['vars'][var_names[0]][0]['comments']:
			file_out.write('\n')
		for var in var_names:
			comments = contents['vars'][var][0]['comments']
			value = contents['vars'][var][0]['value']
			if comments:
				file_out.write('\n')
				file_out.write(comments)
				file_out.write('\n')
			file_out.write('{0}="{1}"'.format(var, base64.b64encode(value)))
			file_out.write('\n')
