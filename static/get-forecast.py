#!/usr/bin/env python3
'''
Author: Chris Haworth
Date: 1/30/2024 (started ~June-July 2021)
Purpose: Gets the forcast data for the local area to the irrigation system. (Need to add params so users can specify City, State, Country)
'''
import json, os, requests
from datetime import date, datetime
from pyowm.owm import OWM

def createLogMessage(message):
	#template for log message to be written to JSON log files
	now = datetime.now()
	newLog = {'date': f'{now.strftime("%m/%d/%Y")}',
			'time': f'{now.strftime("%H:%M:%S")}',
			'message': f'{message}'
		}
	return newLog

def getJsonData(filename):
	'''
	Gets the specified JSON file
	'''
	data = None

	with open(f'/var/www/FlaskServer/static/{filename}.json', 'r') as file:
		data = json.load(file)

	return data

def setJsonData(filename, data):
	'''
	Writes to the specified JSON file
	'''
	with open(f'/var/www/FlaskServer/static/{filename}.json', 'w') as file:
		json.dump(data, file, indent=2, sort_keys=True)

def main():
	#Set Variables
	#get api key
	key = ''
	#key = os.environ.get('WEATHER_API_KEY')
	with open('/var/www/env-var/weather-api-key.json', 'r') as f:
		data = json.load(f)
		key = data['weather-api-key']
	#Set base URL, and location
	url = 'api.openweathermap.org'
	city = 'Raleigh'
	state = 'NC'
	country = 'US'

	#Lists to store important data from the API response.
	fcastdate = [] #date of forecasted weather 
	fcasttime = [] #time of forecasted weather on 'fcastdate'
	pop = [] #percent chance of precipitation
	status = [] #forecasted sky conditions. ie 'clear sky', 'overcast clouds', 'rain', etc
	temperature = [] #outside tempterature in fahrenheit


	#Get latitude, and longitude of specified location
	response = requests.get(f'http://{url}/geo/1.0/direct?q={city},{state},{country}&appid={key}')
	if response.status_code == 200:
		resp = response.json()
		#print(json.dumps(resp,indent=2))
		lat = resp[0]['lat']
		lon = resp[0]['lon']
		units = 'imperial'

		#Get forecast for specified location
		response = requests.get(f'https://{url}/data/2.5/forecast?lat={lat}&lon={lon}&units={units}&appid={key}')
		if response.status_code == 200:
			resp = response.json()
			#print(json.dumps(resp,indent=2))
			forecast = resp['list']
			#print(json.dumps(forecast,indent=2))

			#append inportant forecast inforation to respective lists from response JSON
			for fcast in forecast:
				fcastdate.append(fcast['dt_txt'].split(' ')[0])
				fcasttime.append(fcast['dt_txt'].split(' ')[1])
				pop.append(fcast['pop'])
				status.append(fcast['weather'][0]['description'])
				temperature.append(fcast['main']['temp'])

			#Create JSON objects to store in file with important information lists
			fcastlist = {'forecast' : []}
			for i in range(len(status)):
				fcastlist['forecast'].append({'date' : fcastdate[i],
						'time' : fcasttime[i],
						'status': status[i],
						'pop': int(pop[i] * 100),
						'temp': round(temperature[i], 1)
				})

			#log file to save forcast to
			with open("/var/www/FlaskServer/static/forecast.json", "w") as f:
				json.dump(fcastlist, f, indent=2)
	else:
			#generate logs
			log = getJsonData('water-log')
			log60 = getJsonData('water-log-60-day')
			newLog = createLogMessage(f'Error encountered when trying to retreive geolocation information of {city}, {state}, {country}, thus cannot get weather data.')
			log['log'].append(newLog)
			log60['log'].append(newLog)

			today = getToday()
			log = stripOldLog(log, today, 30)
			log60 = stripOldLog(log60, today, 60)

			#write to log files
			setJsonData('water-log', log)
			setJsonData('water-log-60-day', log60)
	
if __name__ == '__main__':
	main()