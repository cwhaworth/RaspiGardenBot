
import atexit, bcrypt, geopy, json, os, re, requests, sqlite3, time, traceback
from datetime import date, datetime
from geopy.geocoders import Nominatim

dbPath = '/var/www/RaspiGardenBot/database/app_data.db'
weather_api_base = 'https://api.open-meteo.com/v1/forecast'

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

	print(f'API URL:\n{url}')
	return response.json()

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
			print (f'precipitation %: {hour["precipitation_probability"][:-1]}')
			percentRain += int(hour['precipitation_probability'][:-1])
			if int(hour['precipitation_probability'][:-1]) > 50:
				aboveFiddy = True
		if percentRain != 0 and len(data['weather']['hourly']) > 0:
			avgPercentRain = percentRain / len(data['weather']['hourly'])

		print(f'Flow vars:\nsystem_enable: {data["system_enable"]}\naboveFiddy: {aboveFiddy}\navgPercentRain: {avgPercentRain}')

		#perform, and log actions
		if data['system_enable'] == False:
			print("Did not water plants. Water system not enabled.")

		#if it rains: reset last-rained, and write to log
		elif (aboveFiddy and avgPercentRain >= 4.16) or avgPercentRain > 50:
			print(f'Did not water plants due to expected rain in the next 24 hours.'
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
			# GPIO.setup(valve_enable_pin, GPIO.OUT)
			# GPIO.setup(valve_open_pin, GPIO.OUT)
			# GPIO.setup(valve_close_pin, GPIO.OUT)
			# valve = GPIO.PWM(valve_enable_pin, 100) #pin, and Hz

			#turn on pump
			# GPIO.output(pump, GPIO.HIGH)
			time.sleep(data['delay_before'])
			for crop in data["crop_data"]:
				if crop[4] <= data["last_rain"] and data["last_rain"] % crop[4] == 0 and crop[1]:
					# GPIO.setup(crop[3], GPIO.OUT)
					# GPIO.output(crop[3], GPIO.LOW)
					line += f"\"{crop[2]}\", "
			# valve.start(100) #duty cycle
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
			# GPIO.cleanup(valve_enable_pin)
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
			print(line)

		#if get forecast operation returned erroneous
		else:
			update_last_rain(data["last_rain"] + 1)
			print("An error occurred during watering operations.")
		print(f'Ran water_on_schedule() at {str(now)}')
	except Exception as e:
		print(f'Ran into an error while running water_on_schedule() at {str(now)}\ntraceback:\n{traceback.print_exception(e)}')

if __name__ == "__main__":
	water_on_schedule()
