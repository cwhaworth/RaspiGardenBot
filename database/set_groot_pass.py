import bcrypt, sqlite3

password = 'IamGr00t!'

bytes = password.encode('utf-8')

salt = bcrypt.gensalt()

hash = bcrypt.hashpw(bytes, salt)

print(hash)
