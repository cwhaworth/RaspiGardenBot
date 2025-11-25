import  sqlite3, traceback

db_path = '/var/www/RaspiGardenBot/database/app_data.db'
conn = sqlite3.connect(db_path)
cur = conn.cursor()

try:
	rows = cur.execute('select * from system_temp')
	#rows = cur.fetchall()
	if not rows:
		print('No users found')
		conn.close()
		exit()

	for r in rows:
		print(r[2])

	conn.close()


except sqlite3.OperationalError as e:
	print(f'''Error reading users table: {e}\ntraceback:\n{traceback.format_exc()}''')
	conn.close()
	exit()


