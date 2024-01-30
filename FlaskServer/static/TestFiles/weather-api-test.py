from pyowm.owm import OWM
from pyowm.utils.config import get_config_from


#config_dict = get_config_from('weather-api-config.json')
owm = OWM('YOUR-API-KEY-HERE')

mgr = owm.weather_manager()
check = mgr.weather_at_place('Raleigh')
weather = check.weather
print("Weather now: " + str(weather))
