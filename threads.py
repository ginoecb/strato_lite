"""
Repeat these functions until the quit command is entered
"""
import csv, datetime, socket, time
import config as lite
import commands as cmd
import functions as fcn
import predict, queue

def autoThread10():
    ''' Every 10 sec, update data from Ground Station & predict position 30 sec out '''
    # Update data from Ground Station
    lite.grndPos = fcn.getGrndPos(lite.path)
    # Store prediction for position 30 sec
    balloonPos = lite.grndPos
    if lite.n > 1 and fcn.checkUpdate(lite.grndPos, lite.log[lite.n - 1]["grndPos"]):
        balloonPos = lite.predPos
    lite.predQueue.put(predict.predict(balloonPos))
    # Update prediction queue in config.py
    lite.predPos = lite.predQueue.get()
    if (len(lite.predPos) < 4):
        lite.predPos.append(-404)
    time.sleep(10)

def autoThread30():
    ''' Pulls data from APRS, performs calculations, & outputs to .csv file '''
    # Output log to csv
    filename = 'tracking_' + lite.mode + '_' \
               + datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S") + '.csv'
    with open(filename, 'w') as myfile:
        writer = csv.writer(myfile, delimiter=',',
                            lineterminator='\n', quoting=csv.QUOTE_ALL)
        writer.writerow([
            "lat (deg)",
            "lng (deg)",
            "alt (m)",
            "az (deg)",
            "el (deg)",
            "range (m)",
            "ha (deg)",
            "dec (deg)",
            "utime",
            "isotime",
            "grndLat (deg)",
            "grndLng (deg)",
            "grndAlt (m)",
            "aprsLat (deg)",
            "aprsLng (deg)",
            "aprsAlt (m)",
            "predLat (deg)",
            "predLng (deg)",
            "predAlt (m)",
            "command",
            "source"
        ])

        while lite.live:
            fcn.repeat()
            # Send new log[] data to .csv
            data = []
            logData = [
                "pos",
                "azel",
                "hadec",
                "utime",
                "isotime",
                "grndPos",
                "aprsPos",
                "predPos",
                "command",
                "source"
            ]
            for datum in logData:
                # Ensure string values are not extended as char arrays
                if datum == "command" or datum == "source":
                    data.append(lite.log[lite.n][datum])
                else:
                    try:
                        data.extend(lite.log[lite.n][datum])
                    except TypeError:
                        data.append(lite.log[lite.n][datum])
            writer.writerow(data)
            # Flush buffer, force write to .csv
            myfile.flush()
            lite.n += 1
            lite.printed = True
            # Sleep for 28 sec, since 2 sec buffer in repeat()
            time.sleep(28)
        myfile.close()

def userThread():
    ''' Handles mid-flight user commands '''
    options = {
        "h": cmd.listCmds, "help": cmd.listCmds,
        "s": cmd.status, "status": cmd.status,
        "d": cmd.data, "data": cmd.data,
        "o": cmd.offset, "offset": cmd.offset,
        "p": cmd.pause, "pause": cmd.pause,
        "q": cmd.shutdown, "quit": cmd.shutdown,
        "r": cmd.reset, "reset": cmd.reset,
    }
    while lite.live:
        command = input("Type 'h' or 'help' to list commands\n")
        try:
            options[command]()
        except KeyError:
            print("Invalid command\n")
