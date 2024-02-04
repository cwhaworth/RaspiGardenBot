#!/usr/bin/env python3
'''
Author: Chris Haworth
Date: 2/3/2024 (started ~June-July 2021)
Purpose: Uses the forecase data retrieved from 'forecast.json', and parameters defined in 'watering-sectors.json' To decide if and when to water sectors.
If the 'sysEnabled' parameter is disabled, then no watering actions happen.
If 'use-api' is disabled, then water actions are based solely on 'rain-inc'.
Sectors are watered when 'rain-inc' is divided by the number of days since 'last-rained' has a remainder of 0.
If 'use-api' is enabled, and it rained today, then no watering actions are taken and all sector 'rain-inc's are set to 0. 
'''

import json, time
import RPi.GPIO as GPIO
from datetime import date, datetime

GPIO.setmode(GPIO.BCM)
today = str(date.today())
today = today[8 : 10]
now = datetime.now()
#today = '23'

def createLogMessage(message):
	#template for log message to be written to JSON log files
	now = datetime.now()
	newLog = {'date': f'{now.strftime("%m/%d/%Y")}',
			'time': f'{now.strftime("%H:%M:%S")}',
			'message': f'{message}'
		}
	return newLog

def readJson(files):
	#reads a list of files given the names in a list of strings
	fList = []
	for file in files:
		with open(f'/var/www/FlaskServer/static/{file}.json', 'r') as f:
			fList.append(json.load(f))
	return fList[0], fList[1], fList[2]

def writeJson(data):
	#give a list of data sets writes to multiple files where the filename is stored in data['file']
	for d in data['allData']:
		with open(f'/var/www/FlaskServer/static/{d["file"]}.json', 'w') as f:
			json.dump(d['data'], f, indent=2)

def stripOldLog(log, td, inc):
	logDate = datetime.strptime(log['log'][0]['date'], '%m/%d/%Y')
	subDate = td.date() - logDate.date()
	if subDate.days > inc:
		del log['log'][0]
		return stripOldLog(log, td, inc)
	else:
		return log

def finalize(l, l60, sd, files):
	'''
	combines repetative end of script tasks.
	* strip the oldest 30 day log
	* strip the oldest 60 day log
	* writes 30 day log, 60 day log, and sector data to respective JSON files
	'''
	l = stripOldLog(l, now, 30)
	l60 = stripOldLog(l60, now, 60)
	data = {'allData': [{'file': files[0],
			'data': l
			},
			{'file': files[1],
			'data': l60
			},
			{'file': files[2],
			'data': sd
			}]
		}
	writeJson(data)

def main():
	fcast = None
	#log file to read forecast from
	with open('/var/www/FlaskServer/static/forecast.json') as f:
		fcast = json.load(f)
	fcastToday = []
	for fc in fcast['forecast']:
		day = fc['date'][-2 : ]
		if day == today:
			fcastToday.append(fc['pop'])
	percentRain = 0
	count = 0
	avg = 0
	for per in fcastToday:
		percentRain += per
		count += 1
	if percentRain != 0 and count != 0:
		avg = percentRain / count
	#print(f'forecast:\n{fcastToday}')

	#get log data, and sector data from JSON files
	files = ['water-log', 'water-log-60-day', 'watering-sectors']
	log, log60, sectData = readJson(files)

	#perform, and log actions
	if sectData['sysEnable'] == False:
		newLog = createLogMessage("Did not perform water operation. Water system not enabled.")
		log['log'].append(newLog)
		log60['log'].append(newLog)

	#if it rains: reset last-rained, and write to log
	elif sectData['use-api'] == True and len(fcastToday) > 0 and avg >= 50:
		newLog = createLogMessage('Did not water, because it rained today.')
		log['log'].append(newLog)
		log60['log'].append(newLog)
		while len(log) > 30:
			del log[0]
		while len(log60) > 60:
			del log[0]
		sectData['last-rained'] = 0
		finalize(log, log60, sectData, files)

	#If system is enabled, and API data is not in use OR if it does not rain: 
	#water sectors based on interval
	elif sectData['use-api'] == False or len(fcastToday) > 0:
		sectData["last-rained"] += 1
		line = "Watered sector(s): "

		pump = sectData['pump-pin']

		#start watering
		GPIO.setup(pump, GPIO.OUT)
		GPIO.output(pump, GPIO.LOW)
		time.sleep(sectData['delay-before'])
		for sector in sectData["sector"]:
			if sector["rain-inc"] <= sectData["last-rained"] and sectData["last-rained"] % sector["rain-inc"] == 0 and sector['enabled']:
				GPIO.setup(sector['pin'], GPIO.OUT)
				GPIO.output(sector['pin'], GPIO.LOW)
				line += f"\"{sector['id']}\", "
		time.sleep(sectData['water-time'])

		#end watering
		GPIO.cleanup(pump)
		time.sleep(sectData['delay-after'])
		for sector in sectData['sector']:
			if sector['rain-inc'] <= sectData['last-rained'] and sectData['last-rained'] % sector['rain-inc'] == 0 and sector['enabled']:
				GPIO.cleanup(sector['pin'])

		#if API not in use and 30 days have passed, reset last rained
		if sectData['use-api'] == False and sectData['last-rained'] == 30:
			sectData['last-rained'] = 0

		#prepare to write log message to 30 day, and 60 day log files
		line = line[ : -2]
		newLog = createLogMessage(line)
		log['log'].append(newLog)
		log60['log'].append(newLog)
		finalize(log, log60, sectData, files)

	#if get forecast operation returned erroneous
	else:
		sectData['last-rained'] += 1
		newLog = createLogMessage("Forecast data was not initialized correctly. Check for errors in 'forecast.json'.")
		log['log'].append(newLog)
		log60['log'].append(newLog)
		finalize(log, log60, sectData, files)

if __name__ == '__main__':
	main()