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

import bcrypt, json, os, re, sqlite3, time
import RPi.GPIO as GPIO
from datetime import date, datetime
from gpiozero import CPUTemperature
from flask import flash, Flask, jsonify, redirect, render_template, request, session, url_for

app = Flask(__name__)
app.secret_key = os.urandom(24)

dbPath = '/var/www/RaspiGardenBot/database/app_data.db'

bootstrap = {
	"stylesheet": {
		"href": "https://cdn.jsdelivr.net/npm/bootstrap@5.3.8/dist/css/bootstrap.min.css",
		"integrity": "sha384-sRIl4kxILFvY47J16cr9ZwB07vP4J8+LH7qKQnuqkuIAvNWLzeN8tE5YBujZqJLB"
	},	
	"popper": {
		"src": "https://cdn.jsdelivr.net/npm/@popperjs/core@2.11.8/dist/umd/popper.min.js",
		"integrity": "sha384-I7E8VVD/ismYTF4hNIPjVp/Zjvgyol6VFvRkX/vR+Vc4jQkC+hVqc2pM8ODewa9r"
	},
	"javascript": {
		"src": "https://cdn.jsdelivr.net/npm/bootstrap@5.3.8/dist/js/bootstrap.min.js", 
		"integrity": "sha384-G/EV+4j2dNv+tEPo3++6LCgdCROaejBqfUeNjuKAiuXbjrxilcCdDz6ZAVfHWe1Y"
	}
}

GPIO.setmode(GPIO.BCM)

@app.route("/login", methods=['GET', 'POST'])
def login():
	if request.method == 'POST':
		username = request.form['username']
		password = request.form['password']

		#user = getUser(username)
		user = sqlSelectQuery('select id, username, password_hash, priv_level from users where username = ?',
		(username,))
		if user:
			stored_hash = user[2].encode('utf-8')
			if bcrypt.checkpw(password.encode('utf-8'), stored_hash):
				session['user'] = user[1]
				flash('Login successful!', 'success')
				return redirect(url_for('.index'))
			else:
		                flash('Incorrect password.', 'danger')
               			return redirect(url_for('.login'))
		else:
			flash('User not found.', 'danger')
			return redirect(url_for('.login'))
	else:
		styles = getStyles()
		return render_template('login.html', styles=styles)
		# return render_template('login.html', styles=bootstrap)

def logout():
	session.pop('user', None)
	flash('You have been logged out.', 'info')
	return redirect(url_for('.login'))

@app.route("/")
@app.route("/index", methods=['GET', 'POST'])
def index():
	'''
	Home page HTTP handling.
	GET - loads/reloads the page.
	POST - checks which water button was pressed, and waters the desired sectors accordingly. Redirects back to the home the page when done.

	Page contents: Weather data, system data, watering sector data, and manual override buttons for watering.
	'''
	if 'user' not in session:
		return redirect(url_for('.login'))

	if request.method == 'POST':
		for key in request.form.keys():
			if key == 'waterAll':
				waterAll()
			elif key == 'logout':
				return logout()
			elif key.startswith('waterNow_'):
				cropName = key.split('_')[1]
				waterNow(cropName)

		return redirect(url_for('.index'))
	else:
		navURL = getNavURL()
		styles = getStyles()
		now = datetime.now()
		cpu = CPUTemperature()
		temp = round((cpu.temperature * 1.8) + 32, 1) #display temperature in fahrenheit

		data = {
			'api-city': sqlSelectQuery('select val_string from system_params where param = ?', ('api_city',))[0],
			'api-state': sqlSelectQuery('select val_string from system_params where param = ?', ('api_state',))[0],
			'api-country': sqlSelectQuery('select val_string from system_params where param = ?', ('api_country',))[0],
			'use-api': bool(sqlSelectQuery('select val_string from system_params where param = ?', ('use_api',))[0]),
			'last-rain': sqlSelectQuery('select val_num from system_params where param = ?', ('last_rain',))[0],
			'system-enable': bool(sqlSelectQuery('select val_bool from system_params where param = ?', ('system_enable',))[0]),
			'cropData': sqlSelectQuery('select id, enabled, crop, pin, rain_inc from crops', fetchall=True),
			'weather': sqlSelectQuery('select * from forecast', fetchall=True),
			'sysData': sqlSelectQuery('select * from system_temp', fetchall=True),
			'cpuTemp': {
				'time': f'{now.strftime("%H:%M")}',
				'temp': f'{temp} F'
			}
		}

		return render_template('index.html', navurl=navURL, styles=styles, data=data)

def waterAll():
	'''
	Function to water all sectors based on 'water-time' defined in the parameters. 
	'sysEnable', and individual sector 'enabled' parameters must be set to 'true' for any watering action to take place. 
	Waits for 'delay-before' seconds before opening the solenoids to each sector to be watered.
	Waits for 'delay-after' seconds before closing the solenoids to each sector watered.
	Writes log when finished. 
	'''
	# sectData = getJsonData('watering-sectors')
	# pump = sectData['pump-pin']
	# solenoidEnable = sectData['sol-en-pin']
	# solenoidOpen = sectData['sol-open-pin']
	# solenoidClose = sectData['sol-close-pin']

	system_enable = bool(sqlSelectQuery('select val_bool from system_params where param = ?', ('system_enable',))[0])

	# if sectData['sysEnable'] == False:
	if system_enable == False:
		#If watering sytem is not enabled for watering
		# log = getJsonData('water-log')
		# log60 = getJsonData('water-log-60-day')
		# newLog = createLogMessage('Did not perform water operation. Water system not enabled.')
		# log['log'].append(newLog)
		# log60['log'].append(newLog)

		insertLogMessage("Did not perform water operation. Water system not enabled.")

		# today = getToday()
		# log = stripOldLog(log, today, 30)
		# log60 = stripOldLog(log60, today, 60)

		#write to log files
		# setJsonData('water-log', log)
		# setJsonData('water-log-60-day', log60)
	else:
		#pins
		pump = sqlSelectQuery('select val_num from system_params where param = ?', ('pump_pin',))[0]
		valve_enable = sqlSelectQuery('select val_num from system_params where param = ?', ('valve_enable_pin',))[0]
		valve_open = sqlSelectQuery('select val_num from system_params where param = ?', ('valve_open_pin',))[0]
		valve_close = sqlSelectQuery('select val_num from system_params where param = ?', ('valve_close_pin',))[0]

		#timers
		delay_before = sqlSelectQuery('select val_num from system_params where param = ?', ('delay_before',))[0]
		delay_after = sqlSelectQuery('select val_num from system_params where param = ?', ('delay_after',))[0]
		water_time = sqlSelectQuery('select val_num from system_params where param = ?', ('water_time',))[0]

		#crops
		cropData = sqlSelectQuery('select id, enabled, crop, pin, rain_inc from crops', fetchall=True)

		#start watering
		#setup pins for pump and solenoid controller power
		GPIO.setup(pump, GPIO.OUT)
		# GPIO.setup(solenoidEnable, GPIO.OUT)
		# GPIO.setup(solenoidOpen, GPIO.OUT)
		# GPIO.setup(solenoidClose, GPIO.OUT)
		# solenoid = GPIO.PWM(solenoidEnable, 100) #pin, and Hz
		GPIO.setup(valve_enable, GPIO.OUT)
		GPIO.setup(valve_open, GPIO.OUT)
		GPIO.setup(valve_close, GPIO.OUT)
		main_valve = GPIO.PWM(valve_enable, 100) #pin, and Hz

		#turn on pump
		GPIO.output(pump, GPIO.HIGH)

		#open solenoids
		time.sleep(delay_before)
		for crop in cropData:
			if bool(crop[1]) == True:
				GPIO.setup(crop[3], GPIO.OUT)
				GPIO.output(crop[3], GPIO.HIGH)
		main_valve.start(100) #duty cycle
		GPIO.output(valve_open, GPIO.HIGH)
		GPIO.output(valve_close, GPIO.LOW)

		time.sleep(water_time)
		# time.sleep(sectData['delay-before'])
		# for sector in sectData['sector']:
		# 	if sector['enabled'] == True:
		# 		GPIO.setup(sector['pin'], GPIO.OUT)
		# 		GPIO.output(sector['pin'], GPIO.HIGH)
		# solenoid.start(100) #duty cycle
		# GPIO.output(solenoidOpen, GPIO.HIGH)
		# GPIO.output(solenoidClose, GPIO.LOW)

		# time.sleep(sectData['water-time'])

		'''
		end watering
		1. clean up pump output
		2. wait for configured after water operation delay
		3. clean up solenoid and relay output 
		'''
		GPIO.cleanup(pump)
		time.sleep(delay_after)
		GPIO.cleanup(valve_enable)
		GPIO.cleanup(valve_open)
		GPIO.cleanup(valve_close)
		for crop in cropData:
			if bool(crop[1]) == True:
				GPIO.cleanup(crop[3])
		# time.sleep(sectData['delay-after'])
		# GPIO.cleanup(solenoidEnable)
		# GPIO.cleanup(solenoidOpen)
		# GPIO.cleanup(solenoidClose)
		# for sector in sectData['sector']:
		# 	if sector['enabled'] == True:
		# 		GPIO.cleanup(sector['pin'])

		#generate logs
		insertLogMessage('Watered all sectors by manual override.')

		# log = getJsonData('water-log')
		# log60 = getJsonData('water-log-60-day')
		# newLog = createLogMessage('Watered all sectors by manual override.')
		# log['log'].append(newLog)
		# log60['log'].append(newLog)

		# today = getToday()
		# log = stripOldLog(log, today, 30)
		# log60 = stripOldLog(log60, today, 60)

		#write to log files
		# setJsonData('water-log', log)
		# setJsonData('water-log-60-day', log60)

# def waterNow(sectID):
def waterNow(cropName):
	'''
	Function to water selected sector based on 'water-time' defined in the parameters.
	'sysEnable', and sector 'enabled' parameters must be set to 'true' for any watering action to take place.
	Waits for 'delay-before' seconds before opening the solenoids to each sector to be watered.
	Waits for 'delay-after' seconds before closing the solenoids to each sector watered.
	Writes log when finished.
	'''
	# sectData = getJsonData('watering-sectors')
	# pump = sectData['pump-pin']
	# solenoidEnable = sectData['sol-en-pin']
	# solenoidOpen = sectData['sol-open-pin']
	# solenoidClose = sectData['sol-close-pin']

	system_enable = bool(sqlSelectQuery('select val_bool from system_params where param = ?', ('system_enable',))[0])

	# if sectData['sysEnable'] == False:
	if system_enable == False:
		#If watering sytem is not enabled for watering
		# log = getJsonData('water-log')
		# log60 = getJsonData('water-log-60-day')
		# newLog = createLogMessage('Did not perform water operation. Water system not enabled.')
		# log['log'].append(newLog)
		# log60['log'].append(newLog)

		insertLogMessage("Did not perform water operation. Water system not enabled.")

		# today = getToday()
		# log = stripOldLog(log, today, 30)
		# log60 = stripOldLog(log60, today, 60)

		#write to log files
		# setJsonData('water-log', log)
		# setJsonData('water-log-60-day', log60)
	else:
		#pins
		pump = sqlSelectQuery('select val_num from system_params where param = ?', ('pump_pin',))[0]
		valve_enable = sqlSelectQuery('select val_num from system_params where param = ?', ('valve_enable_pin',))[0]
		valve_open = sqlSelectQuery('select val_num from system_params where param = ?', ('valve_open_pin',))[0]
		valve_close = sqlSelectQuery('select val_num from system_params where param = ?', ('valve_close_pin',))[0]

		#timers
		delay_before = sqlSelectQuery('select val_num from system_params where param = ?', ('delay_before',))[0]
		delay_after = sqlSelectQuery('select val_num from system_params where param = ?', ('delay_after',))[0]
		water_time = sqlSelectQuery('select val_num from system_params where param = ?', ('water_time',))[0]		

		#crops 
		cropData = sqlSelectQuery(f'select id, enabled, crop, pin, rain_inc from crops where crop = ?', (cropName,))

		# #get selected sector
		# sectorTemp = {}
		# for sector in sectData['sector']:
		# 	if sector['id'] == sectID:
		# 		sectorTemp = sector
		# 		break

		#start watering
		#setup pins for pump and solenoid controller power
		GPIO.setup(pump, GPIO.OUT)
		GPIO.setup(valve_enable, GPIO.OUT)
		GPIO.setup(valve_open, GPIO.OUT)
		GPIO.setup(valve_close, GPIO.OUT)
		main_valve = GPIO.PWM(valve_enable, 100) #pin, and Hz
		# GPIO.setup(pump, GPIO.OUT)
		# GPIO.setup(solenoidEnable, GPIO.OUT)
		# GPIO.setup(solenoidOpen, GPIO.OUT)
		# GPIO.setup(solenoidClose, GPIO.OUT)
		# solenoid = GPIO.PWM(solenoidEnable, 100) #pin, and Hz

		#turn on pump
		GPIO.output(pump, GPIO.HIGH)
		#open and power solenoid
		time.sleep(delay_before)
		GPIO.setup(cropData[3], GPIO.OUT)
		GPIO.output(cropData[3], GPIO.LOW)
		main_valve.start(100) #duty cycle
		GPIO.output(valve_open, GPIO.HIGH)
		GPIO.output(valve_close, GPIO.LOW)
		# time.sleep(sectData['delay-before'])
		# GPIO.setup(sectorTemp['pin'], GPIO.OUT)
		# GPIO.output(sectorTemp['pin'], GPIO.LOW)
		# solenoid.start(100) #duty cycle
		# GPIO.output(solenoidOpen, GPIO.HIGH)
		# GPIO.output(solenoidClose, GPIO.LOW)

		time.sleep(water_time)

		'''
		end watering
		1. clean up pump output
		2. wait for configured after water operation delay
		3. clean up solenoid and relay output 
		'''
		GPIO.cleanup(pump)
		time.sleep(delay_after)
		GPIO.cleanup(valve_enable)
		GPIO.cleanup(valve_open)
		GPIO.cleanup(valve_close)
		GPIO.cleanup(cropData[3])

		#generate logs
		insertLogMessage(f'Watered sector "{cropName}" by manual override.')

		# log = getJsonData('water-log')
		# log60 = getJsonData('water-log-60-day')
		# newLog = createLogMessage(f'Watered sector "{sectID}" by manual override.')
		# log['log'].append(newLog)
		# log60['log'].append(newLog)

		# today = getToday()
		# log = stripOldLog(log, today, 30)
		# log60 = stripOldLog(log60, today, 60)

		# #write to log files
		# setJsonData('water-log', log)
		# setJsonData('water-log-60-day', log60)

def createLogMessage(message):
	#template for log message to be written to JSON log files
	now = datetime.now()
	newLog = {'date': f'{now.strftime("%m/%d/%Y")}',
			'time': f'{now.strftime("%H:%M:%S")}',
			'message': f'{message}'
		}
	return newLog

def insertLogMessage(message):
	log = (str(date.today()), str(datetime.now().time()), message)
	sqlModifyQuery(f'insert into water_log ("date", "time", message) values {log}')
	sqlModifyQuery(f'insert into water_log_60 ("date", "time", message) values {log}')

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
	if 'user' not in session:
		return redirect(url_for('login'))

	#get stored parameters
	# sectData = getJsonData('watering-sectors')
	data = {
		'api_city' : sqlSelectQuery('select val_string from system_params where param = ?', ('api_city',))[0],
		'api_country' : sqlSelectQuery('select val_string from system_params where param = ?', ('api_country',))[0],
		'api_state' : sqlSelectQuery('select val_string from system_params where param = ?', ('api_state',))[0],
		'delay_after' : sqlSelectQuery('select val_num from system_params where param = ?', ('delay_after',))[0],
		'delay_before' : sqlSelectQuery('select val_num from system_params where param = ?', ('delay_before',))[0],
		'last_rain' : sqlSelectQuery('select val_num from system_params where param = ?', ('last_rain',))[0],
		'max_crops' : sqlSelectQuery('select val_num from system_params where param = ?', ('max_crops',))[0],
		'pump_pin' : sqlSelectQuery('select val_num from system_params where param = ?', ('pump_pin',))[0],
		'valve_close_pin' : sqlSelectQuery('select val_num from system_params where param = ?', ('valve_close_pin',))[0],
		'valve_enable_pin' : sqlSelectQuery('select val_num from system_params where param = ?', ('valve_enable_pin',))[0],
		'valve_open_pin' : sqlSelectQuery('select val_num from system_params where param = ?', ('valve_open_pin',))[0],
		'system_enable' : bool(sqlSelectQuery('select val_num from system_params where param = ?', ('system_enable',))[0]),
		'use_api' : bool(sqlSelectQuery('select val_num from system_params where param = ?', ('use_api',))[0]),
		'water_time' : sqlSelectQuery('select val_num from system_params where param = ?', ('water_time',))[0],
		'crop_data': sqlSelectQuery('select id, enabled, crop, pin, rain_inc from crops', fetchall=True)
	}


	navURL = getNavURL()
	styles = getStyles()
	addButton = False

	if request.method == 'POST':
		#populate data on page based on stored parameters
		# tempData = {'last-rained': sectData['last-rained'],
		# 	'sysEnable': bool(request.form.get('sysEnable', False)),
		# 	'use-api': bool(request.form.get('useAPI', False)),
		# 	'api-city': str(request.form['apiCity']),
		# 	'api-country': str(request.form['apiCountry']),
		# 	'api-state': str(request.form['apiState']),
		# 	'pump-pin': int(request.form['pumpPin']),
		# 	'sol-en-pin': int(request.form['solEnPin']),
		# 	'sol-open-pin': int(request.form['solOpenPin']),
		# 	'sol-close-pin': int(request.form['solClosePin']),
		# 	'max-sectors': int(request.form['maxSectors']),
		# 	'water-time': int(request.form['waterTime']),
		# 	'delay-before': int(request.form['delayBefore']),
		# 	'delay-after': int(request.form['delayAfter']),
		# 	'sector': []
		# }
		tempData = {
			'api_city': str(request.form['api_city']),
			'api_country': str(request.form['api_country']),
			'api_state': str(request.form['api_state']),
			'delay_before': int(request.form['delay_before']),
			'delay_after': int(request.form['delay_after']),
			'last_rain': data['last_rain'],
			'max_crops': int(request.form['max_crops']),
			'pump_pin': int(request.form['pump_pin']),
			'valve_enable_pin': int(request.form['valve_enable_pin']),
			'valve_open_pin': int(request.form['valve_open_pin']),
			'valve_close_pin': int(request.form['valve_close_pin']),
			'system_enable': bool(request.form.get('system_enable', False)),
			'use_api': bool(request.form.get('use_api', False)),
			'water_time': int(request.form['water_time']),
			'crop_data': []
		}
		#consolidate sector data to respective sectors
		# sectID = request.form.getlist('sectorID')
		# sectPin = request.form.getlist('sectorPin')
		# sectInc = request.form.getlist('sectorInc')
		# sectEn = []
		crop_names = request.form.getlist('crop')
		crop_pins = request.form.getlist('crop_pin')
		crop_rain_incs = request.form.getlist('crop_rain_inc')
		crop_enabled_list = []


		# for id in sectID:
		# 	sectEn.append(request.form.get(f'sectorEn_{id}', False))
		for crop in crop_names:
			crop_enabled_list.append(request.form.get(f'crop_enable_{crop}', False))
		for key in request.form.keys():
			# if key.startswith('sectDel_'):
			if key.startswith('cropDel_'):
				#if sector has been deleted
				del_crop_name = key.split('_')[1]
				for i in range(len(crop_names)):
					# crop_temp = {'crop': crop_names[i],
					# 	'pin': int(crop_pins[i]),
					# 	'rain_inc': int(crop_rain_incs[i]),
					# 	'enabled': bool(crop_enabled_list[i])
					# }
					crop_temp = (sqlSelectQuery('select id from crops where crop = ?', (crop_names[i],))[0],
						crop_names[i], int(crop_pins[i]), int(crop_rain_incs[i]), bool(crop_enabled_list[i]))
					if crop_temp[0] != del_crop_name:
						tempData['cropData'].append(crop_temp)
				if len(tempData['crop_data']) < tempData['max_crops']:
					addButton = True

				# delSectID = key.split('_')[1]
				# for i in range(len(sectID)):
				# 	sectTemp = {'id': sectID[i],
				# 		'pin': int(sectPin[i]),
				# 		'rain-inc': int(sectInc[i]),
				# 		'enabled': bool(sectEn[i])
				# 	}
				# 	if sectTemp['id'] != delSectID:
				# 		tempData['sector'].append(sectTemp)
				# if len(tempData['sector']) < tempData['max-sectors']:
				# 	addButton = True
				return render_template('initialize.html', navurl=navURL, styles=styles, data=tempData, addButton=addButton)
				# return render_template('initialize.html', navurl=navURL, styles=bootstrap, data=tempData, addButton=addButton)
			# elif key == 'sectAdd':
			elif key == 'cropAdd':
				#if adding a new sector
				counter = 0
				for i in range(len(crop_names)):
					# crop_temp = {'crop': crop_names[i],
					# 	'pin': int(crop_pins[i]),
					# 	'rain-inc': int(crop_rain_incs[i]),
					# 	'enabled': bool(crop_enabled_list[i])
					# }
					crop_temp = (sqlSelectQuery('select id from crops where crop = ?', (crop_names[i],))[0], 
						crop_names[i], int(crop_pins[i]), int(crop_rain_incs[i]), bool(crop_enabled_list[i]))
					counter = i + 1
					tempData['crop_data'].append(crop_temp)

				# empty = {'crop': counter + 1,
				# 	'pin': 0,
				# 	'rain-inc': 0,
				# 	'enabled': False
				# }
				empty = (counter + 1, 0, 0, False)
				tempData['crop_data'].append(empty)
				if len(tempData['crop_data']) < tempData['max_crops']:
					addButton = True

				# counter = 0
				# for i in range(len(sectID)):
				# 	sectTemp = {'id': sectID[i],
				# 		'pin': int(sectPin[i]),
				# 		'rain-inc': int(sectInc[i]),
				# 		'enabled': bool(sectEn[i])
				# 	}
				# 	counter = i + 1
				# 	tempData['sector'].append(sectTemp)

				# empty = {'id': counter + 1,
				# 	'pin': 0,
				# 	'rain-inc': 0,
				# 	'enabled': False
				# }
				# tempData['sector'].append(empty)
				# if len(tempData['sector']) < tempData['max-sectors']:
				# 	addButton = True
				return render_template('initialize.html', navurl=navURL, styles=styles, sectData=tempData, addButton=addButton)
				# return render_template('initialize.html', navurl=navURL, styles=bootstrap, sectData=tempData, addButton=addButton)
			elif key == 'cropInit':
				#if writing parameters

				if crop_names:
					crop_names_join = ','.join(crop_names)
					sqlModifyQuery(f'delete from crops where crop not in ({crop_names_join})')
				for i in range(len(crop_names)):
					# crop_temp = {'crop': crop_names[i],
					# 	'pin': int(crop_pins[i]),
					# 	'rain-inc': int(crop_rain_incs[i]),
					# 	'enabled': bool(crop_enabled_list[i])
					# }

					if not sqlSelectQuery('select count(*) from crops where crop = ?', (crop_names[i],)):
						insert_crop = (crop_enabled_list[i], crop_names[i], crop_pins[i], crop_rain_incs[i], str(date.today()), str(datetime.now().time()))
						sqlModifyQuery(f'insert into crops (enabled, crop, pin, rain_inc, "date", "time") values {insert_crop}')
					else:
						crop_tuple = (crop_enabled_list[i], crop_names[i], crop_pins[i], crop_rain_incs[i], crop_names[i])
						sqlModifyQuery(f'update crops set enabled = ?, crop = ?, pin = ?, rain_inc = ? where crop = ?')

					crop_temp = (sqlSelectQuery('select id from crops where crop = ?', (crop_names[i],))[0],
						crop_names[i], int(crop_pins[i]), int(crop_rain_incs[i]), bool(crop_enabled_list[i]))
					tempData['crop_data'].append(crop_temp)

				if len(tempData['crop_data']) < tempData['max_crops']:
					addButton = True

				# for i in range(len(sectID)):
				# 	sectTemp = {'id': sectID[i],
				# 		'pin': int(sectPin[i]),
				# 		'rain-inc': int(sectInc[i]),
				# 		'enabled': bool(sectEn[i])
				# 	}
				# 	tempData['sector'].append(sectTemp)

				# setJsonData('watering-sectors', tempData)
				# if len(tempData['sector']) < tempData['max-sectors']:
				# 	addButton = True
				return redirect(url_for('.initialize'))
		# if len(sectData['sector']) < sectData['max-sectors']:
		if len(data['crop_data']) < sectData['max_crops']:
			#toggle to show 'add' button to end of sector list
			addButton = True
		return render_template('initialize.html', navurl=navURL, styles=styles, data=data, addButton=addButton)
		# return render_template('initialize.html', navurl=navURL, styles=bootstrap, data=data, addButton=addButton)
	else:
		# if len(sectData['sector']) < sectData['max-sectors']:
		if len(data['crop_data']) < data['max_crops']:
			addButton = True
		return render_template('initialize.html', navurl=navURL, styles=styles, data=data, addButton=addButton)
		# return render_template('initialize.html', navurl=navURL, styles=bootstrap, data=data, addButton=addButton)

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
	if 'user' not in session:
		return redirect(url_for('login'))

	formButtons = True
	if request.method == 'POST':
		# if 'clear' in request.form.keys():
		# 	#clear 30 day log
		# 	data = {'log': []
		# 	}
		# 	setJsonData('water-log', data)
		# 	return redirect(url_for('.waterLog'))
		# if '60daylog' in request.form.keys():
		# 	#display 60 day log
		# 	formButtons = False
		# 	navURL = getNavURL()
		# 	styles = getStyles()
		# 	waterLog = getJsonData('water-log-60-day')
		# 	return render_template('water-log.html', navurl=navURL, styles=styles, waterLog=waterLog, formButtons=formButtons)
		# if 'back' in request.form.keys():
		# 	return redirect(url_for('.waterLog'))
		if 'clear' in request.form.keys():
			#clear 30 day log
			sqlModifyQuery('delete from water_log')
			return redirect(url_for('.waterLog'))
		if '60daylog' in request.form.keys():
			#display 60 day log
			formButtons = False
			navURL = getNavURL()
			styles = getStyles()
			waterLog = sqlSelectQuery('select * from water_log_60', fetchall=True)
			return render_template('water-log.html', navurl=navURL, styles=styles, waterLog=waterLog, formButtons=formButtons)
			# return render_template('water-log.html', navurl=navURL, styles=bootstrap, waterLog=waterLog, formButtons=formButtons)
		if 'back' in request.form.keys():
			return redirect(url_for('.waterLog'))
	else:
		navURL = getNavURL()
		styles = getStyles()
		# waterLog = getJsonData('water-log')
		waterLog = sqlSelectQuery('select * from water_log', fetchall=True)
		return render_template('water-log.html', navurl=navURL, styles=styles, waterLog=waterLog, formButtons=formButtons)
		# return render_template('water-log.html', navurl=navURL, styles=bootstrap, waterLog=waterLog, formButtons=formButtons)

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
	# styles = url_for('static', filename='styles.css')
	styles = url_for('static', filename='bootstrap.css')

	return styles

def getJsonData(filename):
	'''
	Gets the specified JSON file
	'''
	data = None

	with open(f'/var/www/RaspiGardenBot/static/json/{filename}.json', 'r') as file:
		data = json.load(file)

	return data

def sqlSelectQuery(query, query_params = None, fetchall = False):
	'''
	Gets result of an SQL select query from the SQLite DB
	'''
	conn = sqlite3.connect(dbPath)
	cur = conn.cursor()
	if query_params is not None:
		cur.execute(query, query_params)
	else:
		cur.execute(query)
	result = None
	if fetchall:
		result = cur.fetchall()
	else:
		result = cur.fetchone()
	conn.close()
	return result

def sqlModifyQuery(query, query_params = None):
	'''
	Modifyies or inserts a record into SQLite DB table
	'''
	conn = sqlite3.connect(dbPath)
	cur = conn.cursor()
	if query_params is not None:
		cur.execute(query, query_params)
	else:
		cur.execute(query)
	conn.commit()
	conn.close()

def setJsonData(filename, data):
	'''
	Writes to the specified JSON file
	'''
	with open(f'/var/www/RaspiGardenBot/static/json/{filename}.json', 'w') as file:
		json.dump(data, file, indent=2, sort_keys=True)

if __name__ == '__main__':
	app.run(debug=True)
