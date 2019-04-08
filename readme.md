# Getting Started #
This program tracks an APRS callsign and calculates its next predicted position.
It then sends commands to orient a telescope towards this position over TCP/IP on socket.
Data is also saved throughout the duration of the flight, and is output to a *.csv* file.

Run this with
```
python3 main.py
```

For making a prediction, data will be retrieved from one of the following methods:

- Ground Station, which updates a `.log` file approximately every 10 sec
- APRS, which updates approximately every 30 sec
- Previous predicted values

The source used for a prediction will depend on what *new* data is available,
and will be chosen from those listed with respective decreasing priority.

# Required Modules #
To run this program, the following Python packages are required:

- *csv*
- *datetime*
- *math*
- *numpy*
- *pymap3d*
- *queue*
- *socket*
- *time*
- *urllib*
- *threading*

NOTE: All these packages are available in PyCharm

# Other Requirements #
- A registered key is required for use with *APRS.fi* for callsign tracking
- *predict.py* which requires a `[latitude, longitude, altitude]`
and returns a predicted `[latitude, longitude, altitude]`

# Required Inputs #
At runtime, the program will ask for a text file as input. This should be placed in the **same directory** as the program's files. It should be structured as follows:

1. APRS.fi key
2. Latitude
3. Longitude
4. Altitude
5. Callsign for APRS.fi
6. Callsign for Ground Station
7. Telescope computer's IP Address
8. Telescope computer's Port Number that will listen for packets
9. Path to `.log` file directory

NOTE: Packets will not be sent over TCP/IP if the IP Address and Port Number are left as *Not Set*, or if the computer is unable to connect to the desired machine.

For further reading on how to simulate a launch, see *testing_instructions.md*

# In-flight Commands #
While this program is running, the following commands can be used:

- `d` or `data`: Displays the most recently calculated data
- `p` or `pause`: Pauses telescope movement (toggles on / off)
- `o` or `offset`: Change an applied offset to the predicted HA-DEC
- `r` or `reset`: Orient telescope to its default HA-DEC position (3.66, -6.8)
- `s` or `status`: Display flight setup info
- `q` or `quit`: Exits the program

For further reading on how this program is structured, see *program_structure.md*
