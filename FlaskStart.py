#!/usr/bin/env python3
'''
Author: Chris Haworth
Date: 1/30/2024 (started ~June-July 2021)
Purpose: This Flask application is the front end GUI of my automated garden irrigation system.
There are 3 pages: 
Home - the front page of the Flask app. displays system info, weather data, and watering sector data.
There is also the option to manual override the watering system from here to water one or all sectors immediately.
Initialize - allows user to initialize the parameters the irriagtion system operates under.
Water Log - Displays logs for data on what was watered, and when, as well as errors.
'''

import json, re, time
import RPi.GPIO as GPIO
from datetime import date, datetime
from gpiozero import CPUTemperature
from flask import Flask, jsonify, redirect, render_template, request, url_for

app = Flask(__name__)
GPIO.setmode(GPIO.BCM)

@app.route("/")
@app.route("/index", methods=['GET', 'POST'])
def index():
	'''
	Home page HTTP handling.
	GET - loads/reloads the page.
	POST - checks which water button was pressed, and waters the desired sectors accordingly. Redirects back to the home the page when done.

	Page contents: Weather data, system data, watering sector data, and manual override buttons for watering.
	'''
	if request.method == 'POST':
		for key in request.form.keys():
			if key == 'waterAll':
				waterAll()
			elif key.startswith('waterNow_'):
				sectID = key.split('_')[1]
				waterNow(sectID)

		return redirect(url_for('.index'))
	else:
		navURL = getNavURL()
		styles = getStyles()
		now = datetime.now()
		cpu = CPUTemperature()
		temp = round((cpu.temperature * 1.8) + 32, 1) #display temperature in fahrenheit
		data = {'sectData': None,
			'weather': None,
			'sysData': None,
			'cpuTemp': {
				'time': f'{now.strftime("%H:%M")}',
				'temp': f'{temp} F'
			}
		}
		data['sectData'] = getJsonData('watering-sectors')
		data['weather'] = getForecast(getJsonData('forecast'))
		data['sysData'] = getJsonData('system-data')

		return render_template('index.html', navurl=navURL, styles=styles, data=data)

def waterAll():
	'''
	Function to water all sectors based on 'water-time' defined in the parameters. 
	'sysEnable', and individual sector 'enabled' parameters must be set to 'true' for any watering action to take place. 
	Waits for 'delay-before' seconds before opening the solenoids to each sector to be watered.
	Waits for 'delay-after' seconds before closing the solenoids to each sector watered.
	Writes log when finished. 
	'''
	sectData = getJsonData('watering-sectors')
	pump = sectData['pump-pin']
	soleniod = sectData['sol-pwr-pin']
	if sectData['sysEnable'] == False:
		#If watering sytem is not enabled for watering
		log = getJsonData('water-log')
		log60 = getJsonData('water-log-60-day')
		newLog = createLogMessage('Did not perform water operation. Water system not enabled.')
		log['log'].append(newLog)
		log60['log'].append(newLog)

		today = getToday()
		log = stripOldLog(log, today, 30)
		log60 = stripOldLog(log60, today, 60)

		#write to log files
		setJsonData('water-log', log)
		setJsonData('water-log-60-day', log60)
	else:
		#turn on pump
		GPIO.setup(pump, GPIO.OUT)
		GPIO.output(pump, GPIO.HIGH)
		GPIO.setup(soleniod, GPIO.OUT)
		GPIO.output(soleniod, GPIO.HIGH)
		#open solenoids
		time.sleep(sectData['delay-before'])
		for sector in sectData['sector']:
			if sector['enabled'] == True:
				GPIO.setup(sector['pin'], GPIO.OUT)
				GPIO.output(sector['pin'], GPIO.LOW)
		time.sleep(sectData['water-time'])
		#turn off pump
		GPIO.cleanup(pump)
		GPIO.cleanup(soleniod)
		#close solenoids
		time.sleep(sectData['delay-after'])
		for sector in sectData['sector']:
			if sector['enabled'] == True:
				GPIO.cleanup(sector['pin'])

		#generate logs
		log = getJsonData('water-log')
		log60 = getJsonData('water-log-60-day')
		newLog = createLogMessage('Watered all sectors by manual override.')
		log['log'].append(newLog)
		log60['log'].append(newLog)

		today = getToday()
		log = stripOldLog(log, today, 30)
		log60 = stripOldLog(log60, today, 60)

		#write to log files
		setJsonData('water-log', log)
		setJsonData('water-log-60-day', log60)

def waterNow(sectID):
	'''
	Function to water selected sector based on 'water-time' defined in the parameters. 
	'sysEnable', and sector 'enabled' parameters must be set to 'true' for any watering action to take place. 
	Waits for 'delay-before' seconds before opening the solenoids to each sector to be watered.
	Waits for 'delay-after' seconds before closing the solenoids to each sector watered.
	Writes log when finished. 
	'''
	sectData = getJsonData('watering-sectors')
	pump = sectData['pump-pin']
	soleniod = sectData['sol-pwr-pin']
	if sectData['sysEnable'] == False:
		#If watering sytem is not enabled for watering
		log = getJsonData('water-log')
		log60 = getJsonData('water-log-60-day')
		newLog = createLogMessage('Did not perform water operation. Water system not enabled.')
		log['log'].append(newLog)
		log60['log'].append(newLog)

		today = getToday()
		log = stripOldLog(log, today, 30)
		log60 = stripOldLog(log60, today, 60)

		#write to log files
		setJsonData('water-log', log)
		setJsonData('water-log-60-day', log60)
	else:
		#get selected sector
		sectorTemp = {}
		for sector in sectData['sector']:
			if sector['id'] == sectID:
				sectorTemp = sector
				break
		#turn on pump
		GPIO.setup(pump, GPIO.OUT)
		GPIO.output(pump, GPIO.HIGH)
		GPIO.setup(soleniod, GPIO.OUT)
		GPIO.output(soleniod, GPIO.HIGH)
		#open solenoid
		time.sleep(sectData['delay-before'])
		GPIO.setup(sectorTemp['pin'], GPIO.OUT)
		GPIO.output(sectorTemp['pin'], GPIO.LOW)
		time.sleep(sectData['water-time'])
		#turn off pump
		GPIO.cleanup(pump)
		GPIO.cleanup(soleniod)
		#close solenoid
		time.sleep(sectData['delay-after'])
		GPIO.cleanup(sectorTemp['pin'])

		#generate logs
		log = getJsonData('water-log')
		log60 = getJsonData('water-log-60-day')
		newLog = createLogMessage(f'Watered sector "{sectID}" by manual override.')
		log['log'].append(newLog)
		log60['log'].append(newLog)

		today = getToday()
		log = stripOldLog(log, today, 30)
		log60 = stripOldLog(log60, today, 60)

		#write to log files
		setJsonData('water-log', log)
		setJsonData('water-log-60-day', log60)

def createLogMessage(message):
	#template for log message to be written to JSON log files
	now = datetime.now()
	newLog = {'date': f'{now.strftime("%m/%d/%Y")}',
			'time': f'{now.strftime("%H:%M:%S")}',
			'message': f'{message}'
		}
	return newLog

def getForecast(forecast_json):
	'''
	Returns first 8 entries in the stored forecast data.
	'''
	counter = 0
	weather = []
	for fcast in forecast_json['forecast']:
		if counter == 8:
			break
		else:
			weather.append(fcast)
			counter +=1
	return weather

def stripOldLog(log, today, inc):
	'''
	Removes the oldest log (in days) in the 'log' list based on the 'inc' (increment).
	'''
	logDate = datetime.strptime(log['log'][0]['date'], '%m/%d/%Y')
	subDate = today.date() - logDate.date()
	if subDate.days > inc:
		del log['log'][0]
		return stripOldLog(log, today, inc)
	else:
		return log

@app.route("/initialize", methods=['GET', 'POST'])
def initialize():
	'''
	Initialize page HTTP handling.
	GET - loads/reloads the page.
	POST - depending on which button was pressed:
	* Delete - deletes the sector directly above the button.
	* Add - adds a new sector to the bottom of the list of sectors. If the maximum sectors has been reached then this button does not appear.
	* Initialize - writes changes to irrigation system parameters.

	Page contents: various toggles and text boxes for irrigation system, and individual watering sector parameters.
	'''
	#get stored parameters
	sectData = getJsonData('watering-sectors')
	navURL = getNavURL()
	styles = getStyles()
	addButton = False

	if request.method == 'POST':
		#populate data on page based on stored parameters
		tempData = {'last-rained': sectData['last-rained'],
			'sysEnable': bool(request.form.get('sysEnable', False)),
			'use-api': bool(request.form.get('useAPI', False)),
			'api-city': str(request.form['apiCity']),
			'api-country': str(request.form['apiCountry']),
			'api-state': str(request.form['apiState']),
			'pump-pin': int(request.form['pumpPin']),
			'max-sectors': int(request.form['maxSectors']),
			'water-time': int(request.form['waterTime']),
			'delay-before': int(request.form['delayBefore']),
			'delay-after': int(request.form['delayAfter']),
			'sector': []
		}
		#consolidate sector data to respective sectors
		sectID = request.form.getlist('sectorID')
		sectPin = request.form.getlist('sectorPin')
		sectInc = request.form.getlist('sectorInc')
		sectEn = []
		for id in sectID:
			sectEn.append(request.form.get(f'sectorEn_{id}', False))
		for key in request.form.keys():
			if key.startswith('sectDel_'):
				#if sector has been deleted
				delSectID = key.split('_')[1]
				for i in range(len(sectID)):
					sectTemp = {'id': sectID[i],
						'pin': int(sectPin[i]),
						'rain-inc': int(sectInc[i]),
						'enabled': bool(sectEn[i])
					}
					if sectTemp['id'] != delSectID:
						tempData['sector'].append(sectTemp)
				if len(tempData['sector']) < tempData['max-sectors']:
					addButton = True
				return render_template('initialize.html', navurl=navURL, styles=styles, sectData=tempData, addButton=addButton)
			elif key == 'sectAdd':
				#if adding a new sector
				counter = 0
				for i in range(len(sectID)):
					sectTemp = {'id': sectID[i],
						'pin': int(sectPin[i]),
						'rain-inc': int(sectInc[i]),
						'enabled': bool(sectEn[i])
					}
					counter = i + 1
					tempData['sector'].append(sectTemp)

				empty = {'id': counter + 1,
					'pin': 0,
					'rain-inc': 0,
					'enabled': False
				}
				tempData['sector'].append(empty)
				if len(tempData['sector']) < tempData['max-sectors']:
					addButton = True
				return render_template('initialize.html', navurl=navURL, styles=styles, sectData=tempData, addButton=addButton)
			elif key == 'sectInit':
				#if writing parameters
				for i in range(len(sectID)):
					sectTemp = {'id': sectID[i],
						'pin': int(sectPin[i]),
						'rain-inc': int(sectInc[i]),
						'enabled': bool(sectEn[i])
					}
					tempData['sector'].append(sectTemp)

				setJsonData('watering-sectors', tempData)
				if len(tempData['sector']) < tempData['max-sectors']:
					addButton = True
				return redirect(url_for('.initialize'))
		if len(sectData['sector']) < sectData['max-sectors']:
			#toggle to show 'add' button to end of sector list
			addButton = True
		return render_template('initialize.html', navurl=navURL, styles=styles, sectData=sectData, addButton=addButton)
	else:
		if len(sectData['sector']) < sectData['max-sectors']:
			addButton = True
		return render_template('initialize.html', navurl=navURL, styles=styles, sectData=sectData, addButton=addButton)

@app.route("/water-log", methods=['GET', 'POST'])
def waterLog():
	'''
	Water Log page HTTP handling.
	GET - loads/reloads the page.
	POST - depending on which button was pressed:
	* Clear Log - deletes all items in the 30 day log. Preserves the 60 day log.
	* View 60 Day Log - Changes the log view to the 60 day log.

	Page contents: Log messages collected over both 30, and 60 day periods.
	'''
	formButtons = True
	if request.method == 'POST':
		if 'clear' in request.form.keys():
			#clear 30 day log
			data = {'log': []
			}
			setJsonData('water-log', data)
			return redirect(url_for('.waterLog'))
		if '60daylog' in request.form.keys():
			#display 60 day log
			formButtons = False
			navURL = getNavURL()
			styles = getStyles()
			waterLog = getJsonData('water-log-60-day')
			return render_template('water-log.html', navurl=navURL, styles=styles, waterLog=waterLog, formButtons=formButtons)
		if 'back' in request.form.keys():
			return redirect(url_for('.waterLog'))
	else:
		navURL = getNavURL()
		styles = getStyles()
		waterLog = getJsonData('water-log')
		return render_template('water-log.html', navurl=navURL, styles=styles, waterLog=waterLog, formButtons=formButtons)

def getToday():
	'''
	returns today's date.
	'''
	today = datetime.now()
	return today

def getNavURL():
	'''
	Gets the links for each page on the navigation bar.
	'''
	navURL = {'index': url_for('.index'),
		'init': url_for('.initialize'),
		'waterLog': url_for('.waterLog')
	}

	return navURL

def getStyles():
	'''
	Gets the file for the CSS styles.
	'''
	styles = url_for('static', filename='styles.css')

	return styles

def getJsonData(filename):
	'''
	Gets the specified JSON file
	'''
	data = None

	with open(f'/var/www/RaspiGardenBot/static/json/{filename}.json', 'r') as file:
		data = json.load(file)

	return data

def setJsonData(filename, data):
	'''
	Writes to the specified JSON file
	'''
	with open(f'/var/www/RaspiGardenBot/static/json/{filename}.json', 'w') as file:
		json.dump(data, file, indent=2, sort_keys=True)

if __name__ == '__main__':
	app.run(debug=True)
