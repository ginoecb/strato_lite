"""
Functions shared by LITE files
"""
import datetime, math, socket, queue
import numpy as np
import pymap3d as pm
import time, urllib.request
import predict
import config as lite

def AZELtoHADEC(AZEL):
    ''' Converts coordinates from AZ, EL to HA, DEC '''
    a = AZEL[1]
    z = 90 - a
    A = AZEL[0]
    phi = lite.refPos[0]
    # Python math requires radian values
    zRad = math.radians(z)
    ARad = math.radians(A)
    phiRad = math.radians(phi)
    dec = math.asin(math.cos(zRad) * math.sin(phiRad)
                    + math.sin(zRad) * math.cos(phiRad) * math.cos(ARad))
    ha = math.acos(math.cos(zRad) / (math.cos(dec) * math.cos(phiRad))
                   - math.tan(dec) * math.tan(phiRad))
    ha = math.degrees(ha) / 15.0
    dec = math.degrees(dec)
    if AZEL[0] > 0 and AZEL[0] < 180:
        ha *= -1

    return [ha, dec]

def getGrndPos(data):
    ''' Get latitude, longitude, altitude, and utime from Ground Station '''
    lat = float(data[10])
    lng = float(data[11])
    alt = float(data[14])
    utime = float(data[1])
    return [lat, lng, alt, utime]

def getAprsPos():
    ''' Get latitude, longitude, altitude, and utime from APRS '''
    url = "https://api.aprs.fi/api/get?name=" + lite.callsign + \
          "&what=loc&apikey=" + lite.aprsKey + "&format=xml"
    with urllib.request.urlopen(url) as f:
        text = f.readline()
        # This must be called twice
        text = f.readline()
        if text.find(b'<found>1'):
            outline = text.decode("utf-8")
            outline = outline.replace("<"," ").replace(">"," ")
            line = outline.split()

            lat = lng = alt = utime = None
            i = 0
            while i < len(line):
                if line[i] == 'time' and not utime:
                    i += 1
                    utime = float(line[i])

                elif line[i] == 'lat' and not lat:
                    i += 1
                    lat = float(line[i])

                elif line[i] == 'lng' and not lng:
                    i += 1
                    lng = float(line[i])

                elif line[i] == 'altitude' and not alt:
                    i += 1
                    alt = float(line[i])
                i += 1

        # If callsign data not found
        if not (lat and lng and alt and utime):
            lat = lng = alt = utime = -404
    return [lat, lng, alt, utime]

def checkUpdate(pos, logdata):
    ''' Check if data from Ground Station or APRS has updated '''
    if pos[0:3] == [-404, -404, -404]:
        return False
    elif lite.n > 0:
        if np.array_equal(pos, logdata):
            return False
        else:
            return True
    else:
        return True

def repeat():
    ''' Pull data from Ground Station and APRS & perform calculations '''
    data = {"source": "grnd"}
    # APRS calls are made every 30 sec
    if lite.n % 3 == 0:
        aprsPos = getAprsPos()
    else:
        aprsPos = lite.log[lite.n - 1]["aprsPos"]
    predPos = lite.predQueue.get()
    balloonPos = lite.grndPos
    data["grndPos"] = lite.grndPos[0:3]
    data["aprsPos"] = aprsPos[0:3]
    data["predPos"] = predPos[0:3]

    # Try to get data from Ground Station
    if lite.n > 1 and checkUpdate(lite.grndPos, lite.log[lite.n - 1]["grndPos"]):
        lite.lastGrndUpdate = 0
        if lite.n % 3 == 0:
            if not checkUpdate(aprsPos, lite.log[lite.n - 1]["aprsPos"]):
                lite.lastAprsUpdate += 1
            else:
                lite.lastAprsUpdate = 0
    # Else, try to get data from APRS
    elif lite.n > 1 and checkUpdate(aprsPos, lite.log[lite.n - 1]["aprsPos"]):
        lite.lastGrndUpdate += 1
        if lite.n % 3 == 0:
            lite.lastAprsUpdate = 0
        balloonPos = aprsPos
        data["source"] = "aprs"
    # Else, get data from predicted value
    else:
        lite.lastGrndUpdate += 1
        if lite.n % 3 == 0:
            lite.lastAprsUpdate += 1
        balloonPos = predPos
        balloonPos.append(-404)
        data["source"] = "pred"
    data["pos"] = balloonPos[0:3]
    data["utime"] = balloonPos[3]
    data["isotime"] = datetime.datetime.now()

    # Store new predicted position
    lite.predQueue.put(predict.predict(balloonPos[0:3]))

    # Coordinate conversions
    az, el, range = pm.geodetic2aer(predPos[0], predPos[1], predPos[2],
                                    lite.refPos[0], lite.refPos[1], lite.refPos[2])
    predHADEC = AZELtoHADEC([az, el, range])

    # Add in offset
    predHADEC[0] += lite.offsetHA
    predHADEC[1] += lite.offsetDEC
    # Print HA, DEC
    print("--------------------------------------------\n"
          "   HA: " + str(round(predHADEC[0], 4)) + " deg\n"
                                                    "  DEC: " + str(round(predHADEC[1], 4)) + " deg")
    data["azel"] = [az, el, range]
    data["hadec"] = predHADEC

    time.sleep(1)
    # String command sent to telescope
    strCmd = "#12;"
    # Minimum elevation for telescope movement is 16 deg
    if el >= 16 and not lite.pause and balloonPos != [-404, -404, -404, -404]:
        strCmd = "#33," + str(predHADEC[0]) + "," + str(predHADEC[1]) + ";"
    data["command"] = strCmd
    print(">> " + strCmd + "\n")

    if lite.lastGrndUpdate == 0 and balloonPos != [-404, -404, -404, -404]:
        print("Ground Station data is up to date")
    else:
        print("Ground Station data is not up to date\n"
              "Calls since last Ground Station update: " + str(lite.lastGrndUpdate) + "\n")

    if lite.lastAprsUpdate == 0 and balloonPos != [-404, -404, -404, -404]:
        print("APRS data is up to date")
    else:
        print("APRS data is not up to date\n"
              "Calls since last APRS update: " + str(lite.lastAprsUpdate) + "\n")

    if lite.mode == "actual":
        try:
            lite.sock.send(bytes(strCmd, 'utf-8'))
        except OSError:
            print("Socket closed, packet will not be sent")

    lite.log.append(data)
    time.sleep(1)

def setMode():
    ''' Specify mode to run in main() '''
    print("LITE has two modes for tracking")
    while True:
        mode = input("Run as 'TEST' or 'ACTUAL'?\n")

        ## TEST ##
        if mode.lower() == "test":
            confirm = input("Are you sure you want to begin running TEST?\n"
                            "Type 'yes' to confirm, anything else to re-enter\n")
            if confirm.lower() == "yes":
                print("Running TEST ....\n")
                break

        ## ACTUAL ##
        elif mode.lower() == "actual":
            confirm = input("Telescope will begin moving\n"
                            "Are you sure you want to begin running ACTUAL?\n"
                            "Type 'yes' to confirm, anything else to re-enter\n")
            if confirm.lower() == "yes":
                ## TCP/IP ##
                print("Connecting to telescope ....\n")
                lite.TCP_IP = lite.setVar("IP address")
                lite.TCP_PORT = int(lite.setVar("port number"))
                lite.sock = socket.socket
                lite.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                lite.sock.connect((lite.TCP_IP, lite.TCP_PORT))
                print("Connection established ....\n")
                lite.mode = "actual"
                print("Running ACTUAL ....\n")
                break

        else:
            print("Invalid mode\n")