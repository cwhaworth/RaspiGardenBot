'''
Author: Chris Haworth
Date: 2/3/2024 (started ~June-July 2021)
Purpose: Gets the Raspberry Pi system data to display in Browser GUI.  Keeps track of the most recent 12 readings.
Currently just system temperature. May add more system information as deemed necessary.
'''
import json, time
from datetime import date, datetime
from gpiozero import CPUTemperature

#Get CPU Temp, and current time
cpu = CPUTemperature()
now = datetime.now()

#Open system data storage JSON file
sysData = None
with open('/var/www/FlaskServer/static/system-data.json', 'r') as f:
	sysData = json.load(f)
temp = round((cpu.temperature * 1.8) + 32, 1) #convert CPU temperature from celsius to fahrenheit
#Create JSON object for temperature at the timestamp this script was ran.
temperature = {
	'date': f'{now.strftime("%m/%d/%Y")}',
	'time': f'{now.strftime("%H:%M:%S")}',
	'temp': f'{temp} F'
}
sysData['sysTemp'].append(temperature)

#Remove oldest entry of CPU temp
while len(sysData['sysTemp']) > 12:
	del sysData['sysTemp'][0]

#Write list of CPU temp readings to file
with open('/var/www/FlaskServer/static/system-data.json', 'w') as f:
	json.dump(sysData, f, indent=2, sort_keys=True)
