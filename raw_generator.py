import datetime
import os
from collections import defaultdict

"""
This generates a .html file with a visualization of data from a .csv file.
This file MUST be placed in the same folder as "data.csv"
"""

# These are the config parameters. Change them if you're using a different CSV structure.
# Column numbers of important fields
INPUT_FOLDER = "raw_data"
OUTPUT_FILE_NAME = "visualization.html"
DATA_FIELD = 1

def read_data(f):
    """Yields (date, minute, temp) 3tuples."""
    with open(f) as input_file:
        input_file.readline()
        i = 0
        try:
            for line in input_file:
                fields = line.split(",")

                try:
                    body_temp = float(fields[DATA_FIELD])
                except ValueError:
                    body_temp = -1

                entry_date, entry_time = fields[0].split(" ")
                year, month, day = map(int, entry_date.split("-"))
                hour, minute, second = map(int, entry_time.split(":"))

                # Calculate the date and which minute of the day it is.
                minute_num = hour*60 + minute
                try:
                    date = datetime.datetime(year, month, day)
                except ValueError as e:
                    print day, month, year
                    print
                    print
                    raise e
                i += 1
                yield (date, minute_num, body_temp)
        except Exception as e:
            raise Exception("(Line %d) %s" % (i, str(e)))

def group_by_day(input_files):
    """Returns a dictionary where the date is a key, and the value is a list of (minute_num, temperature) pairs."""
    days = defaultdict(list)
    min_temp = 999
    max_temp = 0
    for f in input_files:
        for line in read_data(f):
            date, minute_num, temp = line
            days[date].append((minute_num, temp))
            if temp > 0 and temp > max_temp:
                max_temp = temp
            if temp > 0 and temp < min_temp:
                min_temp = temp
    return days, min_temp, max_temp

def make_html(input_files, title):
    """Generates an HTML file containing the data."""

    yield "<html><head><title>Visualizing your body</title><style>body {font-family: sans-serif;}</style></head><body>"
    yield "<h1>Visualizing dataset '%s'</h1><table style='border-spacing: 0; white-space:nowrap;'>\n" % title
    days, min_temp, max_temp = group_by_day(input_files)
    for day in sorted(days):

        # Strip out just the important part of the date
        daystr = str(day)[:10]
        yield "<tr><td>%s</td>" % daystr

        # Each minute becomes one cell in the table, colored according to temperature.
        for minute, temp in days[day]:
            if temp > -1:
                temp = color_map(min_temp, max_temp, temp)
                color = "rgb(%d,0,%d)" % (temp, 255-temp)
            else:
                color = "rgb(0,0,0)"
            yield "<td style='background-color:%s;'>" % color 
        yield "</tr>"
    yield "</table>"
    yield "<br><h2>Legend</h2><table><tr>"
    yield "<td style='background-color: rgb(0,0,0); color: white'>Data missing</td>"
    yield key_row(min_temp, max_temp, min_temp)
    yield key_row(min_temp, max_temp, (min_temp*0.75 + max_temp*0.25))
    yield key_row(min_temp, max_temp, (min_temp + max_temp) / 2)
    yield key_row(min_temp, max_temp, (min_temp*0.25 + max_temp*0.75))
    yield key_row(min_temp, max_temp, max_temp)
    yield "</tr></table>"
    yield "</body></html>"

def key_row(l, h, temp):
    return "<td style='background-color: rgb(%d,0,%d); color: white'>%s F</td>" % (color_map(l, h, temp), 255-color_map(l, h, temp), temp)

def color_map(l, h, n):
    """Given a value n in the range [l,h], 
       map n to its corresponding value in the range [0,255].
    """
    return (n - l)/(h-l) * 255

def visualize():
    # Find all files in the input directory
    files = ["%s/%s" % (INPUT_FOLDER, f) for f in os.listdir(INPUT_FOLDER)]

    # Get the column headers from one of the files
    with open(files[0]) as f:
        headers = f.readline().split(",")

    # Clear the output file
    with open(OUTPUT_FILE_NAME, "w") as out:
        out.write("")

    # Write the HTML to the output file.
    with open(OUTPUT_FILE_NAME, "a") as out:
        for string in make_html(files, headers[DATA_FIELD]):
            out.write(string)
    print "Done."


if __name__ == "__main__":
    visualize()