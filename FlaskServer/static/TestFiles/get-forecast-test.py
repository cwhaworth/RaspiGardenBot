from pyowm.owm import OWM

owm = OWM('YOUR-API-KEY-HERE')
#cary_lat = 35.791538
#cary_lon = -78.781120

mgr = owm.weather_manager()
#obs = mgr.weather_at_coords(cary_lat, cary_lon)
#obs = mgr.weather_at_place('Raleigh,US')
#wthr = obs.weather
fcast = mgr.forecast_at_place('Raleigh,US', '3h').forecast

#log file to save forcast to
log = open("weather_log.txt", "w")
log.truncate(0)

#print("Weather now: " + str(wthr))
#fcast.actualize()
for weather in fcast:
	print("Forecast: " + str(weather))
	log.write("Forecast: " + str(weather) + "\n")
#print("Forecast: " + str(fcast))
log.close()
