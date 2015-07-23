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
INPUT_FOLDER = "raw_data" # contains csv files
OUTPUT_FOLDER = "output" # will contain the output website
DATA_FIELDS_NUMBER = [1, 2, 3] # measurement fields which are numbers
DATA_FIELDS_ENUM = [8] # fields whose value is an enumerated set of strings, e.g. sleep.
HTML_HEADER = "<html><head><title>Visualizing your body</title><style>body {font-family: sans-serif;}</style></head><body>"

def read_data(f, col):
  """Yields (date, minute, measurement) 3tuples.
  Measurement is some recorded value, e.g. body heat, air measurement etc."""
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
  """Returns a dictionary where the date is a key, and the value is a list of (minute_num, measurement) pairs."""
  days = defaultdict(list)
  min_measurement = 999
  max_measurement = 0
  for f in input_files:
    for line in read_data(f, col):
      date, minute_num, measurement = line
      days[date].append((minute_num, measurement))
      if measurement > 0 and measurement > max_measurement:
        max_measurement = measurement
      if measurement > 0 and measurement < min_measurement:
        min_measurement = measurement
  return days, min_measurement, max_measurement

def group_by_day_enums(input_files, col):
  """Dictionary of (date, value) pairs. Value is a string. Don't look for min/max."""
  days = defaultdict(list)
  for f in input_files:
    for line in read_data(f, col):
      date, minute_num, measurement = line
      days[date].append((minute_num, measurement))
  return days

def html_numbers(input_files, title, col):
  """Generates an HTML table containing numeric data from all input files."""

  yield "<h1>%s</h1><table style='border-spacing: 0; white-space:nowrap;'>\n" % title
  days, min_measurement, max_measurement = group_by_day_numbers(input_files, col)
  for day in sorted(days):

    # Strip out just the important part of the date
    daystr = str(day)[:10]
    yield "<tr><td>%s</td>" % daystr

    # Each minute becomes one cell in the table, colored according to measurement.
    for minute, measurement in days[day]:
      if measurement > -1:
        measurement = color_map(min_measurement, max_measurement, measurement)
        color = "rgb(%d,0,%d)" % (measurement, 255-measurement)
      else:
        color = "rgb(0,0,0)"
      yield "<td style='background-color:%s;'>" % color
    yield "</tr>"
  yield "</table>"

  # Output a legend showing which values have which color
  yield "<br><h2>Legend</h2><table><tr>"
  yield "<td style='background-color: rgb(0,0,0); color: white'>Data missing</td>"
  yield key_row(min_measurement, max_measurement, min_measurement)
  yield key_row(min_measurement, max_measurement, (min_measurement*0.75 + max_measurement*0.25))
  yield key_row(min_measurement, max_measurement, (min_measurement + max_measurement) / 2)
  yield key_row(min_measurement, max_measurement, (min_measurement*0.25 + max_measurement*0.75))
  yield key_row(min_measurement, max_measurement, max_measurement)
  yield "</tr></table>"


def html_enums(input_files, title, col):
  """Generates an HTML table containing the enumerated string data from all input files."""

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

    # Each minute becomes one cell in the table, colored according to measurement.
    for minute, measurement in days[day]:
      yield "<td style='background-color:%s;'>" % legend[measurement]
    yield "</tr>"
  yield "</table>"
  yield "<br><h2>Legend</h2><table><tr>"

  # Output a legend showing which values have which color
  for measurement, color in legend.items():
    yield "<td style='background-color: %s; color: white'>%s</td>" % (color, measurement)
  yield "</tr></table>"

def key_row(l, h, measurement):
  """Outputs a legend cell for a numeric measurement, showing what color measurements of that value have."""
  return "<td style='background-color: rgb(%d,0,%d); color: white'>%s F</td>" % (color_map(l, h, measurement), 255-color_map(l, h, measurement), measurement)

def color_map(l, h, n):
  """Given a value n in the range [l,h],
     map n to its corresponding value in the range [0,255].
  """
  return (n - l)/(h-l) * 255

def make_index(headers):

  # Make the main index file, which links to the individual dataset files.
  index_file = "%s/index.html" % OUTPUT_FOLDER

  # Overwrite the index file:
  with open(index_file, "w") as out:
    out.write(HTML_HEADER)
    out.write("<h1>Datasets available:</h1><select>")
    out.write("<option value='-'>-</option>")

  # Add a link to each dataset page:
  with open(index_file, "a") as out:
    for col in DATA_FIELDS_ENUM + DATA_FIELDS_NUMBER:
      title = headers[col]
      out.write("<option value='%s'>%s</option>" % (title, title))
    out.write("</select><script src='script.js'></script>")
    out.write("<p><a id='dataset'></a><p><iframe src='' width='900' height='600'><p>Your browser does not support iframes.</p></iframe>")
    out.write("</body></html>")

def visualize():
  # Find all files in the input directory
  print "Reading files from %s..." % INPUT_FOLDER
  files = ["%s/%s" % (INPUT_FOLDER, f) for f in os.listdir(INPUT_FOLDER)]
  print "Reading %d fields across %d files..." % ((len(DATA_FIELDS_ENUM) + len(DATA_FIELDS_NUMBER)), len(files))
  # Get the column headers from one of the files
  with open(files[0]) as f:
    headers = f.readline().split(",")

  # Write the HTML to the output files.
  lines_out = 0
  for cols, fn in [(DATA_FIELDS_NUMBER, html_numbers), (DATA_FIELDS_ENUM, html_enums)]:

      # For each column, create a file that shows that column's dataset across all input data files.
      for col in cols:

        # Clear the output file
        filename = "%s/%s.html" % (OUTPUT_FOLDER, headers[col])
        with open(filename, "w") as out:
          out.write(HTML_HEADER)

        # Write the dataset table
        with open(filename, "a") as out:

          # Write a row to the table. Rows are taken from all days.
          for string in fn(files, headers[col], col):
            out.write(string)
            lines_out += 1
            if lines_out % 10000 == 0:
              print "Writing line %d" % lines_out
          out.write("</body></html>")
        print "Output to %s." % filename
  make_index(headers)


if __name__ == "__main__":
  visualize()
