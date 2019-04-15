import datetime
import queue
import socket
import functions as fcn

## HELPER FUNCTIONS ##
def try_float(value, value_name, prompt):
    ''' Return new input value if float '''
    new_value = fcn.input_out(prompt)
    try:
        return float(new_value)
    except ValueError:
        print(fcn.print_out("Error: " + value_name + " must be a float"))
        return value

def enforce_float(value, value_name):
    ''' Exit 1 if input is not float '''
    try:
        return float(value)
    except ValueError:
        print("Error: " + value_name + " must be a float")
        exit(1)

def enforce_int(value, value_name):
    ''' Exit 1 if input is not float '''
    try:
        return int(value)
    except ValueError:
        print("Error: " + value_name + " must be an int")
        exit(1)

def get_input_file():
    ''' Get input variables from .txt file '''
    filename = input("\nEnter input filename\n")
    file = open(filename, 'r')
    data = file.readlines()
    aprs_key = data[0].strip('\n')
    # Only lat, lng, alt stored as float
    lat = enforce_float(data[1].strip('\n'), "latitude")
    lng = enforce_float(data[2].strip('\n'), "longitude")
    alt = enforce_float(data[3].strip('\n'), "altitude")
    # Other values are string
    aprs_callsign = data[4].strip('\n')
    ground_callsign = data[5].strip('\n')
    TCP_IP = data[6].strip('\n')
    TCP_PORT = data[7].strip('\n')
    log_path = data[8].strip('\n')
    file.close()
    return aprs_key, [lat, lng, alt], aprs_callsign, ground_callsign, TCP_IP, TCP_PORT, log_path

def is_tcp_set(ip_addr, port):
    ''' Check if IP Address and Port Number are set '''
    if ip_addr == "NOT SET" and port == "NOT SET":
        return False
    else:
        return True

def tcp_connect(ip_addr, port, sock):
    ''' Connect to telescope over TCP/IP, if possible '''
    # If IP Address and Port Number are NOT SET, continue without setting up socket
    if is_tcp_set(ip_addr, port):
        port_number = enforce_int(port, "TCP/IP Port Number")
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((ip_addr, port_number))
            print("Connection established ....\n")
        # If the specified IP Address and Port Number are not listening for TCP/IP packets
        except ConnectionRefusedError:
            confirm = input("Failed to connect to telescope, no commands will be sent\n"
                            "Would you still like to continue?\n"
                            "Type 'yes' to continue, anything else to quit\n")
            if confirm.replace(" ", "") != "yes".lower():
                exit(1)
    else:
        print("TCP/IP connection not specified\n"
              "No commands will be sent\n")
    return sock

def init_pred_queue():
    ''' Initialize queue for 30 sec predictions '''
    pred_queue = queue.Queue()
    for i in range(3):
        pred_queue.put(null_pos)
    return pred_queue

# Get data from input file
aprs_key, ref_pos, aprs_callsign, ground_callsign,\
TCP_IP, TCP_PORT, log_path = get_input_file()

# Try connecting to telescope over TCP/IP
sock = socket.socket
sock = tcp_connect(TCP_IP, TCP_PORT, sock)

# Set control variables
live = True
pause = False

# Minimum elevation for valid commands
min_el = 8 # add this to setup.txt

# Current iteration, 10 sec interval
n = 0

# Ensures data has been acquired before accessing
printed = False

'''
log is a list containing data stored throughout the flight
----------------------------------------------------------
Each instance in the list will store a dictionary
containing the following elements:
    pos[]: stores [latitude, longitude, altitude] sent to telescope
    azel[]: stores [azimuth, elevation, range]
    hadec[]: stores [hour angle, declination]
    hadec_offset[]: stores [hour angle offset, declination offset]
    grnd_pos[]: stores [latitude, longitude, altitude] from Ground Station
    aprs_pos[]: stores [latitude, longitude, altitude] from APRS.fi
    pred_pos[]: stores predicted [latitude, longitude, altitude]
    utime: timestamp from Ground Station or APRS packets
    isotime: timestamp from the user's system
    commmand: string sent to the telescope
    source: string for determining source of pos used
'''
log = []

# Null position data
null_pos = [-404, -404, -404, -404]

# Latest position data
ground_pos = null_pos
aprs_pos = null_pos
pred_pos = null_pos

# Store 30 sec predictions in queue
pred_queue = init_pred_queue()

# Number of iterations since last update
last_ground_update = 0
last_aprs_update = 0

# Manual offset
offset_ha = 0
offset_dec = 0

# Next command to be sent to telescope
next_command = "NOT SET"
next_command_valid = False

# Output file for auto_thread_30() and user_thread()
filename = "lite_tracking_commands_" + datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S") + ".txt"
output_file = open(filename, 'w')
