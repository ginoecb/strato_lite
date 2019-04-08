# Testing #

Several testing files are included in the `/testing` directory for simulating flights.

- `listen.py`
- `testing_log_generator_from_csv.py`
- `testing_log_generator_from_existing.py`

# listen.py #

Running `listen.py` will have the user's machine listen for TCP/IP packets on Port 6001.
Any strings sent to this IP and Port will be printed to the terminal, as well as to an output text file.

To use this, open the input text file for `main.py` and set `localhost` as the IP address and `6001` as the Port Number.

# testing_log_generator_from_csv.py #

This script creates a `.log` file in the format of logs saved to the Ground Station during an actual flight.
A `.csv` file with rows of `latitude, longitude, altitude` are required.
Every 10 seconds, a data entry from the `.csv` will be added to the simulated `.log` file.
This can then be used as the input `.log` file for a flight simulation.

To use this, open the input text file for `main.py` and set the input file path as the path to `testing_log_generator_from_csv.log`.
Ensure no header exists in the `.csv` data input file.

# testing_log_generator_from_existing.py #

This script creates a `.log` file in the format of logs saved to the Ground Station during an actual flight.
A `.log` file in the format of the Ground Station's standard output is required.
Every 10 seconds, a data entry from the `.log` will be added to the simulated `.log` file.
This can then be used as the input `.log` file for a flight simulation.

To use this, open the input text file for `main.py` and set the input file path as the path to `testing_log_generator_from_existing.log`.
