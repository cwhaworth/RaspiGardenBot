# RaspiWateringCo
Using a Raspberry Pi 4 B as a solar powered drip irrigation system. UI powered by Flask.

System components:
1. [Raspberry Pi 4B] (https://www.amazon.com/Raspberry-Quad-core-Cortex-A72-Wireless-Bluetooth/dp/B0B6VR1K5Q/ref=sr_1_1_sspa?dib=eyJ2IjoiMSJ9.mP4drOfyakW9P2E6ytjWi6qbtB-JQDqa2RakmAyNa9tJAcW6djw3N7Mbxuj5m0Z1pp3tC8xc7lQ8K-oYj_4xDkK3NQ_hYn6sox-nA_lm98EjgFW9XsW40qSiM9jMYZ5AXPemXuoJrM93NGa0eyANdDVsZgWkITCMb6uMB4x6CNZBXZU-V-L-GxeqoeHB4-4UobSUXVG_TqUqizuZ65FQo49Obb4HO0sqmH2zIL44wuI.Fe1PRRwfBTJyzqSmo1uECJzQFB0CMueahad3Mn_lGfk&dib_tag=se&keywords=raspberry%2Bpi%2B4b&qid=1710653504&sr=8-1-spons&sp_csd=d2lkZ2V0TmFtZT1zcF9hdGY&th=1)
2. [X728 UPS (Compatible with Raspberry Pi 4)] (https://www.amazon.com/Geekworm-Raspberry-Management-Detection-Shutdown/dp/B087FXLZZH?ref_=ast_sto_dp)
3. [X728 Fan HAT] (https://www.amazon.com/Geekworm-Raspberry-Cooling-Expansion-X728-A1/dp/B08B5TQH6W/ref=sr_1_5?crid=X3SJR8OBFVS3&dib=eyJ2IjoiMSJ9.yWMMBgP9gH2a8kxF5aLJXvDxlj6XwnCYpxZaed8Q7hj5FBiW9iD5oCSXTQb6D-HpdU8vUEOJ9RWD2feK-RyIkZvJEZvyeTvibD95QBykx0DZGThCqz2GHwr5sR0RvTOUPdP4PXJ7e5ZEZOQRvMkrv2BJvrsSWhZ1Z_x4S-mENSVEz5W2GfAYsUSBjJjarvn1DXbsDvEyQQaBma5KaZeMGKb2hVDemG4h8V3JrpmINlI.Fp-W44XPAbO879CiTVjuRfe8ru6aicRiCbNf_3I0rBo&dib_tag=se&keywords=x728&qid=1710653101&s=electronics&sprefix=x728%2Celectronics%2C74&sr=1-5)
4. [UPS batteries] (https://www.amazon.com/JESSPOW-Rechargeable-Battery-Batteries-Flashlight/dp/B0CDPVYHJ2?ref_=ast_slp_dp&th=1)
5. Raspberry Pi 4B compatible solar panel assembly; pending 
6. [Soleniods] (https://www.amazon.com/dp/B0CKYRR8Y1?psc=1&ref=ppx_yo2ov_dt_b_product_details)
7. [On/off controller relay] (https://www.amazon.com/JBtek-Channel-Module-Arduino-Raspberry/dp/B00KTEN3TM/ref=sr_1_11?crid=SLHIB9JBB4VP&dib=eyJ2IjoiMSJ9.wOzTK1MHp_Yq1_I3lvNLq4JGgFYSh6bvMOIiSyaiHuQ2Twmqb7oV9QisFD5TFyJQsjtYcHe6HLeWP557mzqSSdpYzKXl68TePFA-cOqPOzfuhwCTwxt8lHsLvLDP9LC7qma2qmHmxHp50dZUcIFKCbOjmIlWp_qUJ1jYqFMQZR-XK654zhvRjb2mYHob5Ptrny6in8E3759kvBHLpT1iN7FWLxmBpjvpGx-LcOb_d-tGlj3MEAE0KOXh6WAWGR-LTKj9sPx8SwN5xB5Gl9l8GqMLhZsk6xcRpqovOIbGFr4.pkR1p878cvPICG-28w08kFQsvnt1_NchNcgogrYFjgk&dib_tag=se&keywords=four+way+relay&qid=1710653229&s=electronics&sprefix=four+way+relay%2Celectronics%2C85&sr=1-11) for solenoids
8. [L298N Motor controller for solenoid open/close] (https://www.amazon.com/dp/B0CR6BX5QL?psc=1&ref=ppx_yo2ov_dt_b_product_details)
9. [Water flow splitter] (https://www.amazon.com/Twinkle-Star-Splitter-Connector-Adapter/dp/B083V1TVM3/ref=sr_1_5?dib=eyJ2IjoiMSJ9.GryOSwr4MhepiM_9OBgwTRFBy1ljhy2XhfylG9LmRlXbuq8JSX7eNhFXIrwp5m5S_FxxN7egwF4Lgj3FPLsT-0-g9FPc-fXANOnuzIske6Bqh9DDHQSpyE183EkuPkiWCm2k5B0bV9CFdxt45FAAw4n5aCkosFmesuqucMu7grqVGa9UJB9T16t5PLhJLuRJKkYNVg22_6X-z05VV088v4eZyFGHJmBpwlvgI_y99lXfbYKbj5z6e_N5gsGF8I0BcSrbMItLQ-FU4kecHqOPvxKwm0Hp3NVGyJdebzx1iBY.4wMvYQu4P5uunkXOG1GtZ0aBoz0g0kN3QZaB-SpjmCE&dib_tag=se&keywords=garden+hose+splitter+4+way&qid=1710653275&sr=8-5)
10. [Water pump] (https://www.amazon.com/gp/product/B07MDBYTLS/ref=ppx_yo_dt_b_search_asin_image?ie=UTF8&psc=1)
11. [Electronics container] (https://www.amazon.com/gp/product/B09TRZ5BTB/ref=ppx_yo_dt_b_search_asin_image?ie=UTF8&psc=1) (is waterproof) x2
12. [IoT Relay surge protector] (https://www.amazon.com/Iot-Relay-Enclosed-High-Power-Raspberry/dp/B00WV7GMA2/ref=sr_1_2_pp?crid=2IZPJUO671ACI&dib=eyJ2IjoiMSJ9.K8SvzXq6lnGT363VsSpZVMubH8ZX7z6Y-RWS-YCJihcZa6owDDQMpZ5TGPKw8E2DKdezX4KbHj0dAlaIedrYjrdMSNDrcOGxxk0VXr4dOdPiBQ5i8Q4dZh0uPdK0kJ7LoCgt0XglFABFrDTDGBLzjRFRHEmSA0wYBMV_w8njYfbpAhX-58bbo_LnBplgPaNQxS2gaV_f7cqJgPZs0SP1lQE2U9Czr_MJFwTJgczm_as.Di4mqweTXOPOa3vvqD2uTt6KAdv15g6tBLE0r_cXZ-o&dib_tag=se&keywords=iot+relay&qid=1710653324&sprefix=iot+rel%2Caps%2C94&sr=8-2)
13. [Waterproof powerbox] (https://www.amazon.com/gp/product/B00274SLK8/ref=ppx_yo_dt_b_search_asin_image?ie=UTF8&psc=1) (for surge protector) 
14. [Jumper wires] (https://www.amazon.com/dp/B07GD1XFWV?ref=ppx_yo2ov_dt_b_product_details&th=1) of various length

Data flow:
1. 'get-forecast.py' retreives 3-hour/5-day forecast, saves all to to 'forecast.json'
2. 'daily-water-control.py' takes the next day forecast, and determines if it will water any sectors
-> 'daily-water-control.py' gets the logic for which sectors it waters from 'watering-sectors.json'
-> 'watering-sectors.json' keeps count of how many days have passed since the last rain as well as the day incriment for each sector
-> new sectors can be added to 'watering-sectors.json' by editing the file or navigating to the "Initialize" page of the flask app
3. 'daily-water-control.py' modifies 'watering-sectors.json' to update/reset the days since the last rain
4. This can also operate without the weather API, and just water based on rain increment

File install instructions (will eventually create install script):
1. Save flask app folder to "/var/www/" directory 
-> Use initialize page to determine which RPi pins you want to use for the sectors, and water flow control 
2. enter command 'crontab -e', and add the following entries:
0 17 * * * /usr/bin/python3 python3 /path/to/get-forcast.py
0 11 * * * /usr/bin/python3 python3 /path/to/daily-water-control.py
0 * * * * /usr/bin/python3 /path/to/get-system-temp.py
@reboot sh /path/to/start.sh
the entries will have 'get-forecast.py' run daily at 5pm, and 'daily-water-control.py' daily the next morning at 11am

Side Notes:
* Use some [wire shrink wrap] (https://www.amazon.com/dp/B08WB2HR66?ref=ppx_yo2ov_dt_b_product_details&th=1) for cable management, and additional waterproofing.
* [Power distribution pinouts] (https://www.amazon.com/dp/B08G1D97YY?psc=1&ref=ppx_yo2ov_dt_b_product_details) is useful for the components involved.
* [Board posts] (https://www.amazon.com/gp/product/B08MF8LDBS/ref=ppx_yo_dt_b_search_asin_image?ie=UTF8&psc=1) will also be useful for mounting.
* I put the X728 in a different container from the Raspberry Pi, and ran cables between to supply power from the UPS. Use 100cm jumper wires.
