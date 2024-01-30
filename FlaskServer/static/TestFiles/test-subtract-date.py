import json
from datetime import datetime

today = datetime.now()
log = None
with open('water-log.json') as f:
	log = json.load(f)
logD = datetime.strptime(log['log'][0]['date'], '%m/%d/%Y')
subDate = today.date() - logD.date()

print(logD.date())
print(today.date())
print(today.date() - logD.date())
if subDate.days > 30:
	print('subDate greater than 30')
