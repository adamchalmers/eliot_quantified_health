import datetime
from collections import defaultdict

"""
This generates a .html file with a visualization of data from a .csv file.
This file MUST be placed in the same folder as "data.csv"
"""

# These are the config parameters. Change them if you're using a different CSV structure.
# Column numbers of important fields
DATA_FIELD = 8
DATE_FIELD = 2
TIME_FIELD = 3
INPUT_FILE_NAME = "data.csv"
OUTPUT_FILE_NAME = "data.html"

def read_data(input_file):
    """Yields (date, minute, temp) 3tuples."""
    for line in input_file:
        fields = line.split(",")

        # If the body temperature's missing, set it to -1.
        try:
            body_temp = int(fields[DATA_FIELD])
        except ValueError:
            body_temp = -1

        # Try to parse the date - skip this line if date's weird.
        try:
            y, mo, d = map(int, fields[DATE_FIELD].split("-"))
            h, mi, _ = map(int, fields[TIME_FIELD].split(":"))
        except ValueError:
            continue

        # Calculate the date and which minute of the day it is.
        minute_num = h*60 + mi
        date = datetime.datetime(y, mo, d)
        yield (date, minute_num, body_temp)

def group_by_day(input_file):
    """Returns a dictionary where the date is a key, and the value is a list of (minute_num, temperature) pairs."""
    days = defaultdict(list)
    for line in read_data(input_file):
        date, minute_num, temp = line
        days[date].append((minute_num, temp))
    return days

def make_html(input_file, title):
    """Generates an HTML file containing the data."""

    yield "<html><head><title>Visualizing your body</title><style>body {font-family: sans-serif;}</style></head><body>"
    yield "<h1>Visualizing dataset '%s'</h1><table style='border-spacing: 0; white-space:nowrap;'>\n" % title
    days = group_by_day(input_file)
    for day in sorted(days):

        # Strip out just the important part of the date
        daystr = str(day)[:10]
        yield "<tr><td>%s</td>" % daystr

        # Each minute becomes one cell in the table, colored according to temperature.
        for minute, temp in days[day]:
            if temp > -1:
                color = "rgb(%d,0,%d)" % (temp, 255-temp)
            else:
                color = "rgb(0,0,0)"
            yield "<td style='background-color:%s;'>" % color 
        yield "</tr>"
    yield "</table>"
    yield "<br><h2>Legend</h2><table><tr>"
    yield "<td style='background-color: rgb(0,0,0); color: white'>Data missing</td>"
    yield "<td style='background-color: rgb(52,0,203); color: white'>29 C</td>"
    yield "<td style='background-color: rgb(157,0,98);'>33 C</td>"
    yield "<td style='background-color: rgb(241,0,14);'>36 C</td>"
    yield "</tr></table>"
    yield "</body></html>"


if __name__ == "__main__":
    input_file = open(INPUT_FILE_NAME)
    headers = input_file.readline().split(",")

    # Clear the output file
    out = open(OUTPUT_FILE_NAME, "w")
    out.write("")
    out.close()

    # Write the HTML to the output file.
    out = open(OUTPUT_FILE_NAME, "a")
    for string in make_html(input_file, headers[DATA_FIELD]):
        out.write(string)
    out.close()
    print "Done."
