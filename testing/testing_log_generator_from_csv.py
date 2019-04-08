import csv
import time

# Simulate .log file by outputting values every 10 seconds
filename_out = "testing_log_generator_from_csv.log"
# Pulls data from existing flight data
filename_in = input("Enter .csv flight data\n")
file_in = open(filename_in, 'r')
i = 0
data = ""
row = ""
# 10 seconds before beginning read/write
time.sleep(10)
# Get data from existing .log data
while True:
    file_out = open(filename_out, 'w')
    print(str(i) + "...")
    row = csv.reader(file_in)
    try:
        # Set variables
        values = next(row)
        latitude = values[0]
        longitude = values[1]
        altitude = values[2]
        utime = str(i)
        # Callsign to track
        source = 'T35T1N6'
        data += ',' + utime + ',,' + source + ',,,,,,,' + latitude + ',' + longitude + ',,,' + altitude + '\n'
        i += 1
        file_out.write(data)
        file_out.close()
        time.sleep(10)
    except StopIteration:
        file_out.close()
        exit(0)