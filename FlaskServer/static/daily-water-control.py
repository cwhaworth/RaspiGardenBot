#!/usr/bin/env python3
import json, time
import RPi.GPIO as GPIO
from datetime import date, datetime


GPIO.setmode(GPIO.BCM)
today = str(date.today())
today = today[8 : 10]
now = datetime.now()
#today = '23'

def readJson(files):
	fList = []
	for file in files:
		with open(f'/var/www/FlaskServer/static/{file}.json', 'r') as f:
			fList.append(json.load(f))
	return fList[0], fList[1], fList[2]

def writeJson(data):
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

#perform, and log actions
files = ['water-log', 'water-log-60-day', 'watering-sectors']
log, log60, sectData = readJson(files)

#if it rains: reset last-rained, and write to log
if sectData['use-api'] == True and len(fcastToday) > 0 and avg >= 50:
	newLog = {'date': f'{now.strftime("%m/%d/%Y")}',
		'time': f'{now.strftime("%H:%M:%S")}',
		'message': f'Did not water, because it rained today.'
	}
	log['log'].append(newLog)
	log60['log'].append(newLog)
	while len(log) > 30:
		del log[0]
	while len(log60) > 60:
		del log[0]

	sectData['last-rained'] = 0

	finalize(log, log60, sectData, files)

#if it does not rain: water sectors based on interval
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
	newLog = {'date': f'{now.strftime("%m/%d/%Y")}',
		'time': f'{now.strftime("%H:%M:%S")}',
		'message': line
	}
	log['log'].append(newLog)
	log60['log'].append(newLog)
	finalize(log, log60, sectData, files)

#if get forecast operation returned erroneous
else:
	sectData['last-rained'] += 1
	newLog = {'date': f'{now.strftime("%m/%d/%Y")}',
		'time': f'{now.strftime("%H:%M:%S")}',
		'message': "Forecast data was not initialized correctly. Check for errors in 'forecast.json'."
	}
	log['log'].append(newLog)
	log60['log'].append(newLog)
	finalize(log, log60, sectData, files)
