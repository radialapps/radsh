# RaDSH is a Rapid Designer for Static HTML.
# Visit the official repositiory at https://github.com/radialapps/radsh
#
# Copyright 2017 (C) RadialApps <radialapps@gmail.com>
#

import re
import sys
import os
import csv

# Regex to be used
regexsquare = r"\[(.*?)\]"
regexcurl = r"{{([^}]+)}}"
regexcaret = r"\^\^([^}]+)\^\^"
regexdollar = r"\$\$(.*?)\$\$"
regexnotdollar = r"\$!(.*?)!\$"

current_row = {}

# Check arguments
if len(sys.argv) != 4:
    print("Wrong number of arguments!\nUsage: python radsh.py <data-csv> <template> <extension>")
    quit()

for i in range(1,3):
    if not os.path.isfile(sys.argv[i]):
        print("File not found --", sys.argv[i])
        quit()

# Read the data
print('Reading data')
with open(sys.argv[1], 'r') as csvfile:
    data_rows = list(csv.reader(csvfile, delimiter=',', quotechar='"'))
    data_columns = data_rows[0]
    del data_rows[0]

# Read the template file
print('Reading template')
with open(sys.argv[2]) as template_file:
    template = template_file.read()

# Replace any unsafe characters for http links
# TODO: expand this to replace other special characters
def replace_special(input):
    return input.replace('&', '&amp;')

# Preprocessing
def preprocess(match):
    match = match.group()

    # Get the string to be processed
    com = match.strip("[]")
    if com[:1] != "#":
        return match

    # Look for conditions
    for col in re.findall(regexcaret, com):
        # Check if such a column exists
        if not col in data_columns:
            continue

        return preprocess_col(col, com)

    print(com, ' -- no match')
    return ''
    
def preprocess_col(col, com):
    if current_row[col] == '1':
        # Answer if true
        return preprocess_answer(regexdollar, com, "true")
    else:
        # Answer if false
        return preprocess_answer(regexnotdollar, com, "false")
            
def preprocess_answer(rx, com, message):
    if len(re.findall(rx, com)) > 0:
        print(col, ' == ' + message + '-- ', re.findall(rx, com)[0])
        return re.findall(rx, com)[0]

# Actual compilation
def compile(match):
    match = match.group()

    # Get the string to be processed
    col = match.strip("{}")

    # Look for things to do
    if col in data_columns:
        # Returned compiled column
        return compile_col(col)
    else:
        # No such column
        return match

def compile_col(col):
    # If a file is to be substituted
    # Throws an error if the file is not found
    if 'file=' in current_row[col]:
        return get_file(col)

    # Return the value of the requested cell
    print (col, ' -- ', current_row[col])

    return escape_http(col)

def get_file(col):
    print ('Inserting file', current_row[col][5:])
    with open(current_row[col][5:]) as fl:
        temp = fl.read()

    # Recursively process the file
    return re.sub(regexcurl,compile, re.sub(regexsquare, preprocess, temp))
        
def escape_http(col):
    # Replace special characters if http link
    # Look for http links and replace special characters
    # TODO: If necessary, replace special characters everywhere
    if current_row[col][:4] == 'http':
        print('Detected http link')
        return replace_special(current_row[col])
    else:
        return current_row[col]

# Main loop
for index, raw_row in enumerate(data_rows):

    # Get the current row
    for i, col in enumerate(data_columns):
        current_row[col] = raw_row[i]

    # Check if something is bad
    if str(current_row['filename']) == 'nan':
        continue;

    # Get the file to save to
    filename = current_row['filename'] + '.' + sys.argv[3]
    print(' ------------ Now working on ', filename, '------------')

    # Start working
    final = re.sub(regexcurl, compile, re.sub(regexsquare, preprocess, template))

    # Write out everything when done
    with open(filename, 'w') as output_file:
        output_file.write(final)

print('Everything done')