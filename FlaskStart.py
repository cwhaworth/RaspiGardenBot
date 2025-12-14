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

import atexit, bcrypt, geopy, json, os, re, requests, sqlite3, time, traceback
import RPi.GPIO as GPIO
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import date, datetime
from geopy.geocoders import Nominatim
from gpiozero import CPUTemperature
from flask import flash, Flask, jsonify, redirect, render_template, request, session, url_for

app = Flask(__name__)
app.secret_key = os.urandom(24)

dbPath = '/var/www/RaspiGardenBot/database/app_data.db'
weather_api_base = 'https://api.open-meteo.com/v1/forecast'

scheduler = BackgroundScheduler()
scheduler.start()
atexit.register(lambda: scheduler.shutdown())

GPIO.setmode(GPIO.BCM)

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

def insertLogMessage(message):
	log = (str(date.today()), str(datetime.now().time()), message)
	sqlModifyQuery(f'insert into water_log ("date", "time", message) values {log}')
	sqlModifyQuery(f'insert into water_log_60 ("date", "time", message) values {log}')

def getCoordinates(): 
	geolocator = Nominatim( user_agent='app')

	city = sqlSelectQuery("select val_string from system_params where param = ?", ("api_city",))[0]
	state = sqlSelectQuery("select val_string from system_params where param = ?", ("api_state",))[0]
	country = sqlSelectQuery("select val_string from system_params where param = ?", ("api_country",))[0]
	
	location = geolocator.geocode(f'{city}, {state}, {country}')
	
	return location.latitude, location.longitude

def get_forecast(current = True, hourly = True, daily = True):
	latitude, longitude = getCoordinates()
	forecast_days = sqlSelectQuery("select val_num from system_params where param = ?", ("api_forecast_days",))[0]
	timezone = sqlSelectQuery("select val_string from system_params where param = ?", ("api_timezone",))[0]
	units = sqlSelectQuery("select val_string from system_params where param = ?", ("api_units",))[0]

	url = (f'{weather_api_base}?latitude={latitude}&longitude={longitude}&forecast_days={forecast_days}&timezone={timezone}')
	if str(units).lower() == 'imperial':
		url += f'&wind_speed_unit=mph&temperature_unit=fahrenheit&precipitation_unit=inch'
	if current:
		url += f'&current=temperature_2m,precipitation,rain,showers,snowfall,cloud_cover'
	if hourly:
		url += f'&hourly=temperature_2m,precipitation_probability,precipitation,cloud_cover'
	if daily:
		url += f'&daily=precipitation_probability_max'
	response = requests.request('GET', url)
	
	# print(f'API URL:\n{url}')
	return response.json()

def update_last_rain(increment):
	update_tuple = (increment, 'last_rain')
	sqlModifyQuery(f'update system_params set val_num = ? where param = ?', update_tuple)

def water_on_schedule():
	now = datetime.now()
	try:
		weather_resp = get_forecast(daily=False)
		data = {
			'use_api': bool(sqlSelectQuery('select val_bool from system_params where param = ?', ('use_api',))[0]),
			'last_rain': sqlSelectQuery('select val_num from system_params where param = ?', ('last_rain',))[0],
			'pump_pin' : sqlSelectQuery('select val_num from system_params where param = ?', ('pump_pin',))[0],
			'system_enable': bool(sqlSelectQuery('select val_bool from system_params where param = ?', ('system_enable',))[0]),
			'crop_data': sqlSelectQuery('select id, enabled, crop, pin, rain_inc from crops', fetchall=True),
			'delay_after' : sqlSelectQuery('select val_num from system_params where param = ?', ('delay_after',))[0],
			'delay_before' : sqlSelectQuery('select val_num from system_params where param = ?', ('delay_before',))[0],
			'sysData': sqlSelectQuery('select * from system_temp', fetchall=True),
			'valve_close_pin' : sqlSelectQuery('select val_num from system_params where param = ?', ('valve_close_pin',))[0],
			'valve_enable_pin' : sqlSelectQuery('select val_num from system_params where param = ?', ('valve_enable_pin',))[0],
			'valve_open_pin' : sqlSelectQuery('select val_num from system_params where param = ?', ('valve_open_pin',))[0],
			'water_time' : sqlSelectQuery('select val_num from system_params where param = ?', ('water_time',))[0],
			'weather': {
				'units': {
					'temp': f'{weather_resp["current_units"]["temperature_2m"]}',
					'cloud_cover': f'{weather_resp["current_units"]["cloud_cover"]}',
					'precipitation': f'{weather_resp["current_units"]["precipitation"][:2]}'
				},
				'current': {
					'date': f'{now.date()}',
					'time': f'{now.time()}'[:-7],
					'temp': f'{weather_resp["current"]["temperature_2m"]}{weather_resp["current_units"]["temperature_2m"]}',
					'cloud_cover': f'{weather_resp["current"]["cloud_cover"]}{weather_resp["current_units"]["cloud_cover"]}',
					'precipitation': f'{weather_resp["current"]["precipitation"]}{weather_resp["current_units"]["precipitation"][:2]}'
				},
				'hourly': []
			}
		}

		for i in range(0, len(weather_resp['hourly']['time'])):
			t = datetime.strptime(weather_resp['hourly']['time'][i], "%Y-%m-%dT%H:%M")
			if t >= now and len(data['weather']['hourly']) < 25:

				data['weather']['hourly'].append({
					'date': t.date(),
					'time': t.time(),
					'temp': (f'{weather_resp["hourly"]["temperature_2m"][i]}'
							f'{weather_resp["hourly_units"]["temperature_2m"]}'),
					'cloud_cover': (f'{weather_resp["hourly"]["cloud_cover"][i]}'
									f'{weather_resp["hourly_units"]["cloud_cover"]}'),
					'precipitation_probability': (f'{weather_resp["hourly"]["precipitation_probability"][i]}'
												f'{weather_resp["hourly_units"]["precipitation_probability"]}'),
					'precipitation': (f'{weather_resp["hourly"]["precipitation"][i]} '
									f'{weather_resp["hourly_units"]["precipitation"][:2]}')
				})
		percentRain = 0
		avgPercentRain = 0
		aboveFiddy = False
		for hour in data['weather']['hourly']:
			percentRain += int(hour['precipitation_probability'][:-1])
			if int(hour['precipitation_probability'][:-1]) > 50:
				aboveFiddy = True
		if percentRain != 0 and len(data['weather']['hourly']) > 0:
			avgPercentRain = percentRain / len(data['weather']['hourly'])

		#perform, and log actions
		if data['system_enable'] == False:
			insertLogMessage("Did not water plants. Water system not enabled.")

		#if it rains: reset last-rained, and write to log
		elif (aboveFiddy and avgPercentRain >= 4.16) or avgPercentRain > 50:
			insertLogMessage(f'Did not water plants due to expected rain in the next 24 hours.'
							f'Any hour above 50%: {"Yes" if aboveFiddy else "No"},' 
							f'Average Percent Chance: {avgPercentRain}%.')
			update_last_rain(0)

		#If system is enabled, and API data is not in use OR if it does not rain: 
		#water crops based on interval
		elif data['use_api'] == False or (not aboveFiddy and avgPercentRain < 4.16) or avgPercentRain <= 50:
			update_last_rain(data["last_rain"] + 1)
			line = "Watered crops(s): "

			pump = data['pump_pin']
			valve_enable_pin = data['valve_enable_pin']
			valve_open_pin = data['valve_open_pin']
			valve_close_pin = data['valve_close_pin']

			#start watering
			#setup pins for pump and solenoid controller power
			# GPIO.setup(pump, GPIO.OUT)
			GPIO.setup(valve_enable_pin, GPIO.OUT)
			# GPIO.setup(valve_open_pin, GPIO.OUT)
			# GPIO.setup(valve_close_pin, GPIO.OUT)
			valve = GPIO.PWM(valve_enable_pin, 100) #pin, and Hz

			#turn on pump
			# GPIO.output(pump, GPIO.HIGH)
			time.sleep(data['delay_before'])
			for crop in data["crop_data"]:
				if crop[4] <= data["last_rain"] and data["last_rain"] % crop[4] == 0 and crop[1]:
					# GPIO.setup(crop[3], GPIO.OUT)
					# GPIO.output(crop[3], GPIO.LOW)
					line += f"\"{crop[2]}\", "
			valve.start(100) #duty cycle
			# GPIO.output(valve_open_pin, GPIO.HIGH)
			# GPIO.output(valve_close_pin, GPIO.LOW)
			time.sleep(data['water_time'])

			'''
			end watering
			1. clean up pump output
			2. wait for configured after water operation delay
			3. clean up solenoid and relay output 
			'''
			# GPIO.cleanup(pump)
			time.sleep(data['delay_after'])
			GPIO.cleanup(valve_enable_pin)
			# GPIO.cleanup(valve_open_pin)
			# GPIO.cleanup(valve_close_pin)
			for crop in data['crop_data']:
				if crop[4] <= data['last_rain'] and data['last_rain'] % crop[4] == 0 and crop[1]:
					# GPIO.cleanup(crop[3])
					continue

			#if API not in use and 30 days have passed, reset last rained
			if data['use_api'] == False and data['last_rain'] == 30:
				update_last_rain(0)

			#prepare to write log message to 30 day, and 60 day log files
			line = line[ : -2]
			insertLogMessage(line)

		#if get forecast operation returned erroneous
		else:
			update_last_rain(data["last_rain"] + 1)
			insertLogMessage("An error occurred during watering operations.")
		print(f'Ran water_on_schedule() at {str(now)}')
	except Exception as e:
		print(f'Ran into an error while running water_on_schedule() at {str(now)}\ntraceback:\n{traceback.print_exc(e)}')

def get_system_temp():
	cpu = CPUTemperature()
	now = datetime.now()
	units = sqlSelectQuery("select val_string from system_params where param = ?", ("api_units",))[0]

	temp = round(cpu.temperature, 1)
	if str(units).lower() == 'imperial':
		temp = round((cpu.temperature * 1.8) + 32, 1) #convert CPU temperature from celsius to fahrenheit

	#Create tuple for temperature at the timestamp this script was ran.
	temperature = (now.strftime("%m/%d/%Y"), now.strftime("%H:%M:%S"), f'{temp}°F')
	
	sqlModifyQuery(f'insert into system_temp ("date", "time", temp) values {temperature}')
	print(f'Checked system temp at {str(now)}')

def getNavURL():
	'''
	Gets the links for each page on the navigation bar.
	'''
	navURL = {'index': url_for('.index'),
		'config': url_for('.config'),
		'waterLog': url_for('.waterLog'),
		'admin': url_for('.admin')
	}

	return navURL

def getStyles():
	'''
	Gets the file for the CSS styles.
	'''
	styles = url_for('static', filename='bootstrap.css')

	return styles

def make_hashbrowns(password):
	bytes = password.encode('utf-8')
	salt = bcrypt.gensalt()
	password_hash = bcrypt.hashpw(bytes, salt)

	if bcrypt.checkpw(password.encode('utf-8'), password_hash):
		return password_hash
	else:
		return None

@app.route("/login", methods=['GET', 'POST'])
def login():
	if request.method == 'POST':
		username = request.form.get('username')
		password = request.form.get('password')

		user = sqlSelectQuery('select id, username, password_hash, priv_level from users where username = ?',
		(username,))
		if user:
			stored_hash = user[2].encode('utf-8')
			if bcrypt.checkpw(password.encode('utf-8'), stored_hash):
				session['user'] = user[1]
				session['priv_level'] = user[3]
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

def logout():
	session.pop('user', None)
	flash('You have been logged out.', 'info')
	return redirect(url_for('.login'))

def waterAll():
	'''
	Function to water all sectors based on 'water-time' defined in the parameters. 
	'sysEnable', and individual sector 'enabled' parameters must be set to 'true' for any watering action to take place. 
	Waits for 'delay-before' seconds before opening the solenoids to each sector to be watered.
	Waits for 'delay-after' seconds before closing the solenoids to each sector watered.
	Writes log when finished. 
	'''
	try:
		system_enable = bool(sqlSelectQuery('select val_bool from system_params where param = ?', ('system_enable',))[0])

		# if sectData['sysEnable'] == False:
		if system_enable == False:
			insertLogMessage("Did not perform water operation. Water system not enabled.")
		else:
			#pins
			pump = sqlSelectQuery('select val_num from system_params where param = ?', ('pump_pin',))[0]
			valve_enable_pin = sqlSelectQuery('select val_num from system_params where param = ?', ('valve_enable_pin',))[0]
			valve_open_pin = sqlSelectQuery('select val_num from system_params where param = ?', ('valve_open_pin',))[0]
			valve_close_pin = sqlSelectQuery('select val_num from system_params where param = ?', ('valve_close_pin',))[0]

			#timers
			delay_before = sqlSelectQuery('select val_num from system_params where param = ?', ('delay_before',))[0]
			delay_after = sqlSelectQuery('select val_num from system_params where param = ?', ('delay_after',))[0]
			water_time = sqlSelectQuery('select val_num from system_params where param = ?', ('water_time',))[0]

			#crops
			cropData = sqlSelectQuery('select id, enabled, crop, pin, rain_inc from crops', fetchall=True)

			#start watering
			#setup pins for pump and solenoid controller power
			# GPIO.setup(pump, GPIO.OUT)
			GPIO.setup(valve_enable_pin, GPIO.OUT)
			# GPIO.setup(valve_open_pin, GPIO.OUT)
			# GPIO.setup(valve_close_pin, GPIO.OUT)
			main_valve = GPIO.PWM(valve_enable_pin, 100) #pin, and Hz

			#turn on pump
			# GPIO.output(pump, GPIO.HIGH)

			#open solenoids
			time.sleep(delay_before)
			for crop in cropData:
				if bool(crop[1]) == True:
					# GPIO.setup(crop[3], GPIO.OUT)
					# GPIO.output(crop[3], GPIO.HIGH)
					continue
			main_valve.start(100) #duty cycle
			# GPIO.output(valve_open_pin, GPIO.HIGH)
			# GPIO.output(valve_close_pin, GPIO.LOW)

			time.sleep(water_time)

			'''
			end watering
			1. clean up pump output
			2. wait for configured after water operation delay
			3. clean up solenoid and relay output 
			'''
			# GPIO.cleanup(pump)
			time.sleep(delay_after)
			GPIO.cleanup(valve_enable_pin)
			# GPIO.cleanup(valve_open_pin)
			# GPIO.cleanup(valve_close_pin)
			for crop in cropData:
				if bool(crop[1]) == True:
					# GPIO.cleanup(crop[3])
					continue

			#generate logs
			insertLogMessage('Watered all sectors by manual override.')
	except Exception as e:
		print(f'Ran into an error while running waterAll()\ntraceback:\n{traceback.print_exc(e)}')

def waterNow(cropName):
	'''
	Function to water selected sector based on 'water-time' defined in the parameters.
	'sysEnable', and sector 'enabled' parameters must be set to 'true' for any watering action to take place.
	Waits for 'delay-before' seconds before opening the solenoids to each sector to be watered.
	Waits for 'delay-after' seconds before closing the solenoids to each sector watered.
	Writes log when finished.
	'''
	try:
		system_enable = bool(sqlSelectQuery('select val_bool from system_params where param = ?', ('system_enable',))[0])

		if system_enable == False:
			insertLogMessage("Did not perform water operation. Water system not enabled.")
		else:
			#pins
			pump = sqlSelectQuery('select val_num from system_params where param = ?', ('pump_pin',))[0]
			valve_enable_pin = sqlSelectQuery('select val_num from system_params where param = ?', ('valve_enable_pin',))[0]
			valve_open_pin = sqlSelectQuery('select val_num from system_params where param = ?', ('valve_open_pin',))[0]
			valve_close_pin = sqlSelectQuery('select val_num from system_params where param = ?', ('valve_close_pin',))[0]

			#timers
			delay_before = sqlSelectQuery('select val_num from system_params where param = ?', ('delay_before',))[0]
			delay_after = sqlSelectQuery('select val_num from system_params where param = ?', ('delay_after',))[0]
			water_time = sqlSelectQuery('select val_num from system_params where param = ?', ('water_time',))[0]		

			#crops 
			cropData = sqlSelectQuery(f'select id, enabled, crop, pin, rain_inc from crops where crop = ?', (cropName,))

			#start watering
			#setup pins for pump and solenoid controller power
			# GPIO.setup(pump, GPIO.OUT)
			GPIO.setup(valve_enable_pin, GPIO.OUT)
			# GPIO.setup(valve_open_pin, GPIO.OUT)
			# GPIO.setup(valve_close_pin, GPIO.OUT)
			main_valve = GPIO.PWM(valve_enable_pin, 100) #pin, and Hz

			#turn on pump
			# GPIO.output(pump, GPIO.HIGH)

			#open and power solenoid
			time.sleep(delay_before)
			# GPIO.setup(cropData[3], GPIO.OUT)
			# GPIO.output(cropData[3], GPIO.LOW)
			main_valve.start(100) #duty cycle
			# GPIO.output(valve_open_pin, GPIO.HIGH)
			# GPIO.output(valve_close_pin, GPIO.LOW)

			time.sleep(water_time)

			'''
			end watering
			1. clean up pump output
			2. wait for configured after water operation delay
			3. clean up solenoid and relay output 
			'''
			# GPIO.cleanup(pump)
			time.sleep(delay_after)
			GPIO.cleanup(valve_enable_pin)
			# GPIO.cleanup(valve_open_pin)
			# GPIO.cleanup(valve_close_pin)
			# GPIO.cleanup(cropData[3])

			#generate logs
			insertLogMessage(f'Watered sector "{cropName}" by manual override.')
	except Exception as e:
		print(f'Ran into an error while running waterNoe() for {cropName}\ntraceback:\n{traceback.print_exc(e)}')

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
			if key == 'logout':
				return logout()
			elif key == 'userSettings':
				return userSettings()
			elif key == 'waterAll':
				waterAll()
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
		
		weather_resp = get_forecast()

		data = {
			'api_city': sqlSelectQuery('select val_string from system_params where param = ?', ('api_city',))[0],
			'api_state': sqlSelectQuery('select val_string from system_params where param = ?', ('api_state',))[0],
			'api_country': sqlSelectQuery('select val_string from system_params where param = ?', ('api_country',))[0],
			'use_api': bool(sqlSelectQuery('select val_bool from system_params where param = ?', ('use_api',))[0]),
			'last_rain': sqlSelectQuery('select val_num from system_params where param = ?', ('last_rain',))[0],
			'system_enable': bool(sqlSelectQuery('select val_bool from system_params where param = ?', ('system_enable',))[0]),
			'cropData': sqlSelectQuery('select id, enabled, crop, pin, rain_inc from crops', fetchall=True),
			'weather': {
				'units': {
				'temp': f'{weather_resp["current_units"]["temperature_2m"]}',
				'cloud_cover': f'{weather_resp["current_units"]["cloud_cover"]}',
				'precipitation': f'{weather_resp["current_units"]["precipitation"][:2]}',
				'precipitaion_probability_max': f'{weather_resp["daily_units"]["precipitation_probability_max"]}'
				},
				'current': {
					'date': f'{now.date()}',
					'time': f'{now.time()}'[:-7],
					'temp': f'{weather_resp["current"]["temperature_2m"]}{weather_resp["current_units"]["temperature_2m"]}',
					'cloud_cover': f'{weather_resp["current"]["cloud_cover"]}{weather_resp["current_units"]["cloud_cover"]}',
					'precipitation': f'{weather_resp["current"]["precipitation"]}{weather_resp["current_units"]["precipitation"][:2]}',
					'precipitation_probability_max': ''
					
				},
				'hourly': []
			},
			'sysData': sqlSelectQuery('select * from system_temp', fetchall=True),
			'cpuTemp': {
				'time': f'{now.strftime("%H:%M")}',
				'temp': f'{temp} F'
			}
		}
		for i in range(0, len(weather_resp['daily']['time'])):
			t = datetime.strptime(weather_resp['daily']['time'][i], "%Y-%m-%d")
			if t.date() == now.date():
				data['weather']['current']['precipitation_probability_max'] = (f'{weather_resp["daily"]["precipitation_probability_max"][i]}'
																			f'{weather_resp["daily_units"]["precipitation_probability_max"]}')
				break
		for i in range(0, len(weather_resp['hourly']['time'])):
			t = datetime.strptime(weather_resp['hourly']['time'][i], "%Y-%m-%dT%H:%M")
			if t >= now and len(data['weather']['hourly']) < 13:

				data['weather']['hourly'].append({
					'date': t.date(),
					'time': t.time(),
					'temp': (f'{weather_resp["hourly"]["temperature_2m"][i]}'
							f'{weather_resp["hourly_units"]["temperature_2m"]}'),
					'cloud_cover': (f'{weather_resp["hourly"]["cloud_cover"][i]}'
									f'{weather_resp["hourly_units"]["cloud_cover"]}'),
					'precipitation_probability': (f'{weather_resp["hourly"]["precipitation_probability"][i]}'
												f'{weather_resp["hourly_units"]["precipitation_probability"]}'),
					'precipitation': (f'{weather_resp["hourly"]["precipitation"][i]} '
									f'{weather_resp["hourly_units"]["precipitation"][:2]}')
				})

		return render_template('index.html', navurl=navURL, styles=styles, session=session, data=data)

@app.route("/config", methods=['GET', 'POST'])
def config():
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

	timezones = [
		"auto", "GMT+0", 
		"America%2FAnchorage", "America%2FLos_Angeles", "America%2FDenver", "America%2FChicago", "America%2FNew_York", "America%2FSao_Paulo",
		"Europe%2FLondon", "Europe%2FBerlin", "Europe%2FMoscow",
		"Africa%2FCairo",
		"Asia%2FBangkok", "Asia%2FSingapore", "Asia%2FTokyo",
		"Australia%2FSydney",
		"Pacific%2FAuckland"
	]

	#get stored parameters
	data = {
		'api_city' : sqlSelectQuery('select val_string from system_params where param = ?', ('api_city',))[0],
		'api_country' : sqlSelectQuery('select val_string from system_params where param = ?', ('api_country',))[0],
		'api_forecast_days': sqlSelectQuery('select val_num from system_params where param = ?', ('api_forecast_days',))[0],
		'api_state' : sqlSelectQuery('select val_string from system_params where param = ?', ('api_state',))[0],
		'api_timezone' : sqlSelectQuery('select val_string from system_params where param = ?', ('api_timezone',))[0],
		'api_units' : sqlSelectQuery('select val_string from system_params where param = ?', ('api_units',))[0],
		'delay_after' : sqlSelectQuery('select val_num from system_params where param = ?', ('delay_after',))[0],
		'delay_before' : sqlSelectQuery('select val_num from system_params where param = ?', ('delay_before',))[0],
		'hours': list(range(24)),
		'max_crops' : sqlSelectQuery('select val_num from system_params where param = ?', ('max_crops',))[0],
		'pump_pin' : sqlSelectQuery('select val_num from system_params where param = ?', ('pump_pin',))[0],
		'system_enable' : bool(sqlSelectQuery('select val_bool from system_params where param = ?', ('system_enable',))[0]),
		'timezones': timezones,
		'use_api' : bool(sqlSelectQuery('select val_bool from system_params where param = ?', ('use_api',))[0]),
		'valve_close_pin' : sqlSelectQuery('select val_num from system_params where param = ?', ('valve_close_pin',))[0],
		'valve_enable_pin' : sqlSelectQuery('select val_num from system_params where param = ?', ('valve_enable_pin',))[0],
		'valve_open_pin' : sqlSelectQuery('select val_num from system_params where param = ?', ('valve_open_pin',))[0],
		'water_schedule_hour' : sqlSelectQuery('select val_string from system_params where param = ?', ('water_schedule_hour',))[0],
		'water_time' : sqlSelectQuery('select val_num from system_params where param = ?', ('water_time',))[0],
		'crop_data': sqlSelectQuery('select id, enabled, crop, pin, rain_inc from crops', fetchall=True)
	}

	navURL = getNavURL()
	styles = getStyles()
	addButton = False

	if request.method == 'POST':
		#populate data on page based on stored parameters
		tempData = {
			'api_city': str(request.form['api_city']),
			'api_country': str(request.form['api_country']),
			'api_forecast_days': int(request.form['api_forecast_days']),
			'api_state': str(request.form['api_state']),
			'api_timezone': f"{str(request.form['api_timezone'])}",
			'api_units': str(request.form['api_units']),
			'delay_before': int(request.form['delay_before']),
			'delay_after': int(request.form['delay_after']),
			'hours': list(range(24)),
			'max_crops': int(request.form['max_crops']),
			'pump_pin': int(request.form['pump_pin']),
			'system_enable': bool(request.form.get('system_enable', False)),
			'timezones': timezones,
			'use_api': bool(request.form.get('use_api', False)),
			'valve_enable_pin': int(request.form['valve_enable_pin']),
			'valve_open_pin': int(request.form['valve_open_pin']),
			'valve_close_pin': int(request.form['valve_close_pin']),
			'water_schedule_hour': str(request.form['water_schedule_hour']),
			'water_time': int(request.form['water_time']),
			'crop_data': []
		}
		#consolidate crop data to respective crop data values
		crop_names = request.form.getlist('crop_name')
		crop_pins = request.form.getlist('crop_pin')
		crop_rain_incs = request.form.getlist('crop_rain_inc')
		crop_enabled_list = []

		for crop in crop_names:
			crop_enabled_list.append(request.form.get(f'crop_enable_{crop}', False))
		for key in request.form.keys():
			if key == 'logout':
				return logout()
			elif key == 'userSettings':
				return userSettings()
			elif key.startswith('cropDel_'):
				#if sector has been deleted
				del_crop_name = key.split('_')[1]
				for i in range(len(crop_names)):
					if crop_names[i] != del_crop_name:
						crop_temp = (sqlSelectQuery('select id from crops where crop = ?', (crop_names[i],))[0],
							bool(crop_enabled_list[i]), crop_names[i], int(crop_pins[i]), int(crop_rain_incs[i]))
						tempData['crop_data'].append(crop_temp)
				if len(tempData['crop_data']) < tempData['max_crops']:
					addButton = True

				return render_template('config.html', navurl=navURL, styles=styles, data=tempData, addButton=addButton)
			elif key == 'cropAdd':
				#if adding a new crop
				counter = 0
				for i in range(len(crop_names)):
					crop_temp = (sqlSelectQuery('select id from crops where crop = ?', (crop_names[i],))[0], 
						bool(crop_enabled_list[i]), crop_names[i], int(crop_pins[i]), int(crop_rain_incs[i]))
					counter = i + 1
					tempData['crop_data'].append(crop_temp)

				empty = (9999, False, "Plant!", 0, 0)
				tempData['crop_data'].append(empty)
				if len(tempData['crop_data']) < tempData['max_crops']:
					addButton = True

				return render_template('config.html', navurl=navURL, styles=styles, data=tempData, addButton=addButton)
			elif key == 'cropSave':
				#if writing parameters
				for key, value in tempData.items():
					if (key != "crop_data" and key != 'hours' and key != 'timezones'):
						val = None
						# print(f'key: {key}, val: {value}')
						if isinstance(tempData[key], bool):
							val = "val_bool"
						elif isinstance(tempData[key], int):
							val = "val_num"
						elif isinstance(tempData[key], str):
							val = "val_string"
						param_tuple = (value, key)
						sqlModifyQuery(f'update system_params set {val} = ? where param = ?', param_tuple)

				if crop_names:
					crop_names_join = ','.join(crop_names)
					crop_names_db = sqlSelectQuery('select id, crop from crops', fetchall=True)
					for crop in crop_names_db:
						if crop[1] not in crop_names_join:
							sqlModifyQuery(f'delete from crops where crop = ?', (crop[1],))
				for i in range(len(crop_names)):

					if sqlSelectQuery('select count(*) from crops where crop = ?', (crop_names[i],))[0] == 0:
						insert_crop = (crop_enabled_list[i], crop_names[i], crop_pins[i], crop_rain_incs[i], str(date.today()), str(datetime.now().time().strftime('%H:%M:%S')))
						sqlModifyQuery(f'insert into crops (enabled, crop, pin, rain_inc, "date", "time") values {insert_crop}')
					else:
						crop_tuple = (crop_enabled_list[i], crop_names[i], crop_pins[i], crop_rain_incs[i], crop_names[i])
						sqlModifyQuery(f'update crops set enabled = ?, crop = ?, pin = ?, rain_inc = ? where crop = ?', crop_tuple)

					crop_temp = (sqlSelectQuery('select id from crops where crop = ?', (crop_names[i],))[0],
						crop_names[i], int(crop_pins[i]), int(crop_rain_incs[i]), bool(crop_enabled_list[i]))
					tempData['crop_data'].append(crop_temp)

				if len(tempData['crop_data']) < tempData['max_crops']:
					addButton = True

				return redirect(url_for('.config'))

		if len(data['crop_data']) < sectData['max_crops']:
			#toggle to show 'add' button to end of sector list
			addButton = True
		return render_template('config.html', navurl=navURL, styles=styles, data=data, addButton=addButton)
	else:
		if len(data['crop_data']) < data['max_crops']:
			addButton = True
		return render_template('config.html', navurl=navURL, styles=styles, data=data, addButton=addButton)

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
		return redirect(url_for('.login'))

	formButtons = True
	if request.method == 'POST':
		for key in request.form.keys():
			match key:
				case 'logout':
					return logout()
				case "userSettings":
					return userSettings()
				case 'clear':
					#clear 30 day log
					sqlModifyQuery('delete from water_log')
					return redirect(url_for('.waterLog'))
				case '60daylog':
					#display 60 day log
					formButtons = False
					navURL = getNavURL()
					styles = getStyles()
					waterLog = sqlSelectQuery('select * from water_log_60 order by date desc, time desc', fetchall=True)
					return render_template('water-log.html', navurl=navURL, styles=styles, waterLog=waterLog, formButtons=formButtons)
				case 'back':
					return redirect(url_for('.waterLog'))
		return redirect(url_for('.waterLog'))
	else:
		navURL = getNavURL()
		styles = getStyles()
		waterLog = sqlSelectQuery('select * from water_log order by date desc, time desc', fetchall=True)
		return render_template('water-log.html', navurl=navURL, styles=styles, waterLog=waterLog, formButtons=formButtons)

@app.route("/admin", methods=['GET', 'POST'])
def admin():
	if 'user' not in session:
		return redirect(url_for('.login'))

	edit = {
		'edit': False,
		'username': ''
		}
	navURL = getNavURL()
	styles = getStyles()
	user_sql_resp = sqlSelectQuery('select id, username, password_hash, priv_level from users', fetchall=True)
	user_data = []
	for user in user_sql_resp:
		user_data.append({
			'username': user[1],
			'password_hash': f'*******...{user[2][-5:]}',
			'priv_level': user[3]
		})
	
	if request.method == "POST":
		for key in request.form.keys():
			match key:
				case "logout":
					return logout()
				case "userSettings":
					return userSettings()
				case "editUser":
					edit['edit'] = True
					edit['username'] = request.form.get('username')
					return render_template('admin.html', navurl=navURL, styles=styles, session=session, user_data=user_data, edit=edit)
				case "saveUser":
					username = request.form.get('username')
					new_priv = request.form.get(f'privLevel')
					user_tuple = (new_priv, username)
					sqlModifyQuery('update users set priv_level = ? where username = ?', user_tuple)
					return redirect(url_for('.admin'))
				case "cancel":
					return redirect(url_for('.admin'))
				case "delUser":
					sqlModifyQuery('delete from users where username = ?', (request.form.get('username'),))
					return redirect(url_for('.admin'))
				case "addUser":
					new_user = request.form.get('username')
					new_password = request.form.get('password')
					new_priv_level = request.form.get('priv_level')
					password_hash = make_hashbrowns(new_password)
					if password_hash:
						user_tuple = (new_user, password_hash.decode('utf-8'), new_priv_level)
						sqlModifyQuery(f'insert into users (username, password_hash, priv_level) values {user_tuple}')
					return redirect(url_for('.admin')) 
			
		return redirect(url_for('.admin'))
	else:
		return render_template('admin.html', navurl=navURL, styles=styles, session=session, user_data=user_data, edit=edit) 

@app.route("/userSettings", methods=['GET', 'POST'])
def userSettings():
	if 'user' not in session:
		return redirect(url_for('.login'))

	navURL = getNavURL()
	styles = getStyles()
	user_sql_resp = sqlSelectQuery('select id, username, password_hash, priv_level from users where username = ?', (session['user'],))
	
	print(user_sql_resp)
	if request.method == "POST":
		for key in request.form.keys():
			match key:
				case "logout":
					return logout()
				case "userSettings":
					return redirect(url_for('.userSettings'))
				case "changePass":
					oldPass = request.form.get('oldPass')
					newPass = request.form.get('newPass')

					if bcrypt.checkpw(oldPass.encode('utf-8'), user_sql_resp[2].encode('utf-8')):
						newPass_hash = make_hashbrowns(newPass)
						user_tuple = (newPass_hash.decode('utf-8'), user_sql_resp[1])
						sqlModifyQuery('update users set password_hash = ? where username = ?', user_tuple)

		return redirect(url_for('.userSettings'))
	else:
		return render_template('user-settings.html', navurl=navURL, styles=styles, session=session)

def init_jobs():
	def check_job(job):
		if scheduler.get_job(job_id=job):
			scheduler.remove_job(job_id=job)
		
	check_job("get_system_temp")
	check_job("water_on_schedule")

	scheduler.add_job(
		id="get_system_temp",
		func=get_system_temp,  
		trigger="cron", 
		hour='*', 
		minute='0',
		# minute='*',
		second='0',
		replace_existing=True)

	scheduler.add_job(
		id="water_on_schedule",
		func=water_on_schedule,  
		trigger="cron", 
		hour=sqlSelectQuery('select val_string from system_params where param = "water_schedule_hour"')[0], 
		minute='0',
		# hour='*',
		# minute='*',
		# second='0',
		replace_existing=True)

init_jobs()

if __name__ == '__main__':
	app.run(debug=False, use_reloader=False)
