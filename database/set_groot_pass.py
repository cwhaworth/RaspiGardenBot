import bcrypt, sqlite3, traceback

db_path = '/var/www/RaspiGardenBot/database/app_data.db'
conn = sqlite3.connect(db_path)
cur = conn.cursor()

try:
	cur.execute('select id, username, password_hash from users')
	rows = cur.fetchall()
	if not rows:
		print('No users found')
		conn.close()
		exit()

	for r in rows:
		print(f'uid: {r[0]}\nusername: {r[1]}\npt_pass: {r[2]}')
		uid = r[0]
		username = r[1]
		pt_pass = r[2]

		bytes = pt_pass.encode('utf-8')
		salt = bcrypt.gensalt()
		hash = bcrypt.hashpw(bytes, salt)

		check = 'IamGr00t!'.encode('utf-8')

		if bcrypt.checkpw(check, hash):
			hashed_str = hash.decode('utf-8')
			cur.execute('update users set password_hash = ? where id = ?', 
					(hashed_str, uid)
			)

			print('Set password for groot user')
			conn.commit()

		print(hash)

	conn.close()


except sqlite3.OperationalError as e:
	print(f'''Error reading users table: {e}\ntraceback:\n{traceback.format_exc()}''')
	conn.close()
	exit()



