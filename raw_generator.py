import datetime
import os
import subprocess
import string
from collections import defaultdict

"""
This generates a .html file with a visualization of data from a .csv file.
This file MUST be placed in the same folder as "data.csv"
"""

# These are the config parameters. Change them if you're using a different CSV structure.
# Column numbers of important fields
INPUT_FOLDER = "raw_data"
OUTPUT_FILE_NAME = "visualization.html"
DATA_FIELDS_NUMBER = [1, 2, 3]
DATA_FIELDS_ENUM = [8]

def read_data(f, col):
  """Yields (date, minute, temp) 3tuples."""
  with open(f) as input_file:
    input_file.readline()
    i = 0
    try:

      # 'line' will typically look like:
      # 2015-04-01 23:58:00,94.1,92.8,56,0,5.41,1.0,,deep,
      for line in input_file:
        fields = line.split(",")


        # If the field starts with letters, assume it's string data.
        # Otherwise try to make it a number
        # Otherwise turn it into -1
        if len(fields[col]) > 0 and fields[col][0] in string.letters:
          measurement = fields[col]
        else:
          try:
            measurement = float(fields[col])
          except ValueError:
            measurement = -1

        # Find the date/time this row takes place in
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
        yield (date, minute_num, measurement)
    except Exception as e:
      print "(Line %d) %s in file %s" % (i, str(e), f)
      raise e

def group_by_day_numbers(input_files, col):
  """Returns a dictionary where the date is a key, and the value is a list of (minute_num, temperature) pairs."""
  days = defaultdict(list)
  min_temp = 999
  max_temp = 0
  for f in input_files:
    for line in read_data(f, col):
      date, minute_num, temp = line
      days[date].append((minute_num, temp))
      if temp > 0 and temp > max_temp:
        max_temp = temp
      if temp > 0 and temp < min_temp:
        min_temp = temp
  return days, min_temp, max_temp

def group_by_day_enums(input_files, col):
  """Dictionary of (date, value) pairs. Value is a string. Don't look for min/max."""
  days = defaultdict(list)
  for f in input_files:
    for line in read_data(f, col):
      date, minute_num, measurement = line
      days[date].append((minute_num, measurement))
  return days

def make_html_numbers(input_files, title, col):
  """Generates an HTML file containing the data."""

  yield "<h1>Visualizing dataset '%s'</h1><table style='border-spacing: 0; white-space:nowrap;'>\n" % title
  days, min_temp, max_temp = group_by_day_numbers(input_files, col)
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


def make_html_enums(input_files, title, col):
  """Generates an HTML file containing the data."""

  legend = {"rem": "#33CCFF",
        "light": "#3399FF",
        "deep": "#3366FF",
        "unknown": "#8c8c8c",
        "interruption": "#0f0",
        "": "#aaa",
        -1: "#000",
        }

  yield "<h1>Visualizing dataset '%s'</h1><table style='border-spacing: 0; white-space:nowrap;'>\n" % title
  days = group_by_day_enums(input_files, col)
  for day in sorted(days):

    # Strip out just the important part of the date
    daystr = str(day)[:10]
    yield "<tr><td>%s</td>" % daystr

    # Each minute becomes one cell in the table, colored according to temperature.
    for minute, measurement in days[day]:
      yield "<td style='background-color:%s;'>" % legend[measurement]
    yield "</tr>"
  yield "</table>"
  yield "<br><h2>Legend</h2><table><tr>"
  for measurement, color in legend.items():
    yield "<td style='background-color: %s; color: white'>%s</td>" % (color, measurement)
  yield "</tr></table>"

def key_row(l, h, temp):
  return "<td style='background-color: rgb(%d,0,%d); color: white'>%s F</td>" % (color_map(l, h, temp), 255-color_map(l, h, temp), temp)

def color_map(l, h, n):
  """Given a value n in the range [l,h],
     map n to its corresponding value in the range [0,255].
  """
  return (n - l)/(h-l) * 255

def visualize():
  # Find all files in the input directory
  print "Reading files from %s..." % INPUT_FOLDER
  files = ["%s/%s" % (INPUT_FOLDER, f) for f in os.listdir(INPUT_FOLDER)]
  print "Reading %d fields across %d files..." % ((len(DATA_FIELDS_ENUM) + len(DATA_FIELDS_NUMBER)), len(files))
  # Get the column headers from one of the files
  with open(files[0]) as f:
    headers = f.readline().split(",")

  # Clear the output file
  with open(OUTPUT_FILE_NAME, "w") as out:
    out.write("<html><head><title>Visualizing your body</title><style>body {font-family: sans-serif;}</style></head><body>")

  # Write the HTML to the output file.
  lines_out = 0
  with open(OUTPUT_FILE_NAME, "a") as out:
    for col in DATA_FIELDS_NUMBER:
        for string in make_html_numbers(files, headers[col], col):
          out.write(string)
          lines_out += 1
          if lines_out % 10000 == 0:
            print "Writing line %d" % lines_out
    for col in DATA_FIELDS_ENUM:
        for string in make_html_enums(files, headers[col], col):
          out.write(string)
          lines_out += 1
          if lines_out % 10000 == 0:
            print "Writing line %d" % lines_out
    out.write("</body></html>")
  print "Output to %s." % OUTPUT_FILE_NAME

if __name__ == "__main__":
  visualize()
