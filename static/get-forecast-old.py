import json, os
from pyowm.owm import OWM

#api key
key = os.environ.get('WEATHER_API_KEY')
owm = OWM(f'{key}')

#api call
mgr = owm.weather_manager()
fcast = mgr.forecast_at_place('Raleigh,US', '3h').forecast

fcastdate = []
fcasttime = []
status = []
for line in fcast:
	#extract forecast reference_time and status from API response
	reftime = str(line).find('reference_time=')
	refstatus = str(line).find('status=')
	reftimeend = str(line).find('+')
	refstatend = str(line).find(', d')

	fcastdatetime = str(line)[reftime : reftimeend].replace('reference_time=', '').split(" ")
	fcastdate.append(fcastdatetime[0])
	fcasttime.append(fcastdatetime[1])
	status.append(str(line)[refstatus : refstatend].replace('status=', ''))

fcastlist = {'forecast' : []}
for i in range(len(status)):
	fcastlist['forecast'].append({'date' : fcastdate[i],
			'time' : fcasttime[i],
			'status': status[i]
	})

#log file to save forcast to
with open("/var/www/FlaskServer/static/forecast.json", "w") as f:
	json.dump(fcastlist, f, indent=2)
