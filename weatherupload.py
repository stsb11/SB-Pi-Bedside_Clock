# Add this script to another Pi which has a Sense HAT plugged into it, and leave it running for live weather data.
# INSTRUCTIONS: 
# sudo su, then SSH from the Sense HAT pi into the bedside clock pi so that it's added as a known host at least once.
# pip3 install paramiko (IMPORTANT: Do this as root user, otherwise the cron will fail)
# Add this to the root cron (sudo crontab -e): @reboot    python3 /home/pi/weather/weatherupload.py >> /home/pi/cronlog.txt 2<&1
# Put the right IP address, username and password in the writeNew() function.

print ("WEATHER.PY - Starting up...")
from sense_hat import SenseHat
import time
from datetime import datetime
import os
import paramiko

print("Waiting 30s to let network finish coming up...")
time.sleep(30)
print("DONE. Starting weather logging...")

ssh = paramiko.SSHClient()

def writeNew():
    print("Attempting to connect via SSH...")
    ssh.load_host_keys(os.path.expanduser(os.path.join("~", ".ssh", "known_hosts")))
    ssh.connect("IP ADDRESS HERE", username="pi", password="raspberry")
    sftp = ssh.open_sftp()
    sftp.put("pFile.txt", "/home/pi/pFile.txt")
    sftp.put("hFile.txt", "/home/pi/hFile.txt")
    sftp.put("tFile.txt", "/home/pi/tFile.txt")
    sftp.close()
    ssh.close()
    when = datetime.now()
    print(str(when) + " - update complete. Waiting 15 mins...")

def trimLog(fileName):
    mx = 100 # Max number of lines in the file.
    my_file = open(fileName, "r")
    items = my_file.readlines()
    my_file.close()

    if len(items) > mx:
        newList = []
        x = 0
        for item in items:
            if x > 0 and x <= mx:
                newList.append(item)
            x = x + 1

        with open(fileName, 'w') as f:
            for theData in newList:
                f.write('%s' % theData)

sense = SenseHat()
sense.clear()

while True:
    pressure = sense.get_pressure()
    temp = sense.get_temperature()
    humid = sense.get_humidity()

    if pressure > 900 and pressure < 1060:
        pFile = open('pFile.txt', 'a')
        pFile.write(str(int(pressure)) + '\n')
        pFile.close()
        trimLog('pFile.txt')

    if temp >= -20 and temp <= 80:
        tFile = open('tFile.txt', 'a')
        tFile.write(str(int(temp)) + '\n')
        tFile.close()
        trimLog('tFile.txt')

    if humid >= 0 and humid <= 110:
        hFile = open('hFile.txt', 'a')
        hFile.write(str(int(humid)) + '\n')
        hFile.close()
        trimLog('hFile.txt')

    writeNew()
    time.sleep(60*15)
