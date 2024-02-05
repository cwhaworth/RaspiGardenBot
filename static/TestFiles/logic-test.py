import json
from datetime import date
from datetime import datetime

#log file to read forcast from
log = open("weather_log.txt", "r")
fcast = log.readlines()
fcastToday = ""
log.close()

for line in fcast:
	#extract forecast reference_time and status from file read
	reftime = line.find("reference_time=")
	refstatus = line.find("status=")
	reftimeend = line.find("+")
	refstatend = line.find(", d")

	time = line[reftime : reftimeend]
	status = line[refstatus : refstatend]
	time = time.replace("reference_time=", "")
	status = status.replace("status=", "")

	#isolate system date, and forecast time
	foreDate = time[8 : 10]
	foreHour = time[11 : 13]
	today = str(date.today())
	today = today[8 : 10]
#	today = str(24)

	if foreDate == today:
		fcastToday += str(time) + ", " + str(status) + "\n"

	#print to test extraction
	#print("time: " + str(time) + ", status: " + str(status))
	#print("Today's date: " + str(today) + ", Forecast date: " + str(foreDate) + ", Forecast hour: " + str(foreHour))

#perform and log actions
#print(str(fcastToday))
log = open('water-log.txt', 'a')
sectData = None
with open('watering-sectors.json', 'r') as f:
	sectData = json.load(f)
now = datetime.now()

#print(str(sectData))
if fcastToday != '' and "rain" in fcastToday:
	log.write(now.strftime("%d/%m/%Y %H:%M:%S") + " did not water because it rained today.\n")
	sectData["last-rained"] = 0
	#print(fcastToday[ : 10] + " -> water the plants, and perform other logical functions.")
	with open('watering-sectors-test.json', 'w') as f:
		json.dump(sectData, f)

elif fcastToday != '':
	log.write(now.strftime("%d/%m/%Y %H:%M:%S") + "watered sector(s): ")
	for sector in sectData["sector"]:
		if sector["rain-inc"] <= sectData["last-rained"]:
			log.write(str(sector["id"]) + ", ")
	log.write("\n")
	sectData["last-rained"] += 1
	#print(fcastToday[ : 10] + " -> do not water the plants, and perform other logical functions.")
	with open('watering-sectors-test.json', 'w') as f:
		json.dump(sectData, f)

else:
	sectData["last-rained"] += 1
	#print(fcastToday[ : 10] + " -> forecast data was not initialized correctly. correct error in 'get-forecast.py'")
	with open('watering-sectors-test.json', 'w') as f:
		json.dump(sectData, f)
	log.write(now.strftime("%d/%m/%Y %H:%M:%S") + "forecast data was not initialized correctly. correct error in 'get-forecast.py'.\n")

log.close()
