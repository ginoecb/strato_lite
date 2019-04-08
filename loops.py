import config as lite
import datetime
import functions as fcn
import numpy as np
import predict
import time
import urllib

def every_10_ground():
    ''' Update Ground Station data '''
    lite.ground_pos = fcn.get_ground_pos()

def every_10_else():
    ''' Update prediction data and save data to lite.log[] '''
    data = {}
    # Check all sources for relevant data
    pos = fcn.get_updated_data(data)
    data['pos'] = pos[0:3]
    data['utime'] = pos[3]
    data['isotime'] = datetime.datetime.now()
    # Update prediction queue
    lite.pred_pos = lite.pred_queue.get()
    lite.pred_queue.put(predict.predict(pos))
    # Calculate AZEL and HADEC values
    hadec = fcn.get_hadec(pos, data)
    # Output data to .csv
    data['ground_pos'] = lite.ground_pos[0:3]
    data['aprs_pos'] = lite.aprs_pos[0:3]
    data['pred_pos'] = lite.pred_pos[0:3]
    # Set command to be sent to telescope
    lite.next_command = "NOT SET"
    if not np.array_equal(pos, lite.null_pos) and not np.array_equal(pos, fcn.get_last_pred_pos()):
        lite.next_command = "#33," + str(data['hadec'][0]) + "," + str(data['hadec'][1]) + ";"
    data['command'] = lite.next_command
    # Check if command is valid to send
    lite.next_command_valid = fcn.is_command_valid(pos, data['azel'][1])
    # Update lite.log[]
    lite.log.append(data)

def every_30_aprs():
    ''' Update data from APRS '''
    # Update data from APRS
    try:
        lite.aprs_pos = fcn.get_aprs_pos()
    except urllib.error.URLError:
        print(fcn.print_out("Failed to fetch data from APRS.fi\n"))

def every_30_else():
    ''' Send command to telescope '''
    # Send command to telescope, if connected and meeting minimum elevation requirement
    if lite.is_tcp_set(lite.TCP_IP, lite.TCP_PORT) and lite.next_command_valid and lite.next_command != "NOT SET":
        # '#33,HA,DEC;' Provides values for HA, DEC to telescope
        lite.sock.send(bytes(lite.next_command, 'utf-8'))
        time.sleep(1)
        # '#12;' Commands telescope to point towards current HA, DEC
        lite.sock.send(bytes("#12;", 'utf-8'))
        time.sleep(1)
