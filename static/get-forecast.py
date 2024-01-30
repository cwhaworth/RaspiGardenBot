#!/usr/bin/env python3
import json, os, requests
from pyowm.owm import OWM

#api key
#key = os.environ.get('WEATHER_API_KEY')
key = ''
with open('/var/www/env-var/weather-api-key.json', 'r') as f:
	data = json.load(f)
	key = data['weather-api-key']
url = 'api.openweathermap.org'
city = 'Raleigh'
state = 'NC'
country = 'US'

fcastdate = []
fcasttime = []
pop = []
status = []
temperature = []

response = requests.get(f'http://{url}/geo/1.0/direct?q={city},{state},{country}&appid={key}')
if response.status_code == 200:
	resp = response.json()
	#print(json.dumps(resp,indent=2))
	lat = resp[0]['lat']
	lon = resp[0]['lon']
	units = 'imperial'

	response = requests.get(f'https://{url}/data/2.5/forecast?lat={lat}&lon={lon}&units={units}&appid={key}')
	if response.status_code == 200:
		resp = response.json()
		#print(json.dumps(resp,indent=2))

		forecast = resp['list']
		#print(json.dumps(forecast,indent=2))

		for fcast in forecast:
			fcastdate.append(fcast['dt_txt'].split(' ')[0])
			fcasttime.append(fcast['dt_txt'].split(' ')[1])
			pop.append(fcast['pop'])
			status.append(fcast['weather'][0]['description'])
			temperature.append(fcast['main']['temp'])

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
