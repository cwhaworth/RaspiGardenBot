# RaspiWateringCo
Using a Raspberry Pi 4 B as a solar powered drip irrigation system. UI powered by Flask.

System components:
1. Raspberry Pi 4B; obtained
2. Raspberry Pi 4B compatible UPS; obtained
3. Raspberry Pi 4B compatible solar panel assembly; pending
4. drip irrigation kit; pending 
5. soleniods; pending
6. On/off controller relay for solenoids; obtained
8. Electronics container; obtained
9. Short ciruit protection; ?, need more research

Data flow:
1. 'get-forecast.py' retreives 3-hour/5-day forecast, saves all to to 'forecast.json'
2. 'daily-water-control.py' takes the next day forecast, and determines if it will water any sectors
-> 'daily-water-control.py' gets the logic for which sectors it waters from 'watering-sectors.json'
-> 'watering-sectors.json' keeps count of how many days have passed since the last rain as well as the day incriment for each sector
-> new sectors can be added to 'watering-sectors.json' by editing the file or navigating to the "Initialize" page of the flask app
3. 'daily-water-control.py' modifies 'watering-sectors.json' to update/reset the days since the last rain

File install instructions:
1. Save flask app folder to "/var/www/" directory 
-> Use initialize page to determine which RPi pins you want to use for the sectors, and water flow control 
2. enter command 'crontab -e', and add the following entries:
0 17 * * * python3 ~/path/to/get-forcast.py
0 11 * * * python3 ~/path/to/daily-water-control.py
the entries will have 'get-forecast.py' run daily at 5pm, and 'daily-water-control.py' daily the next morning at 11am
3. For the flask app enter command "export FLASK_APP=FlaskStart.py"
