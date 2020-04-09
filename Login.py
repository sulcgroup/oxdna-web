from __future__ import print_function
from datetime import date, datetime, timedelta
import mysql.connector
import time
import bcrypt

cnx = mysql.connector.connect(user='root', password='', database='azdna')
cursor = cnx.cursor()

query = ("SELECT id, password FROM Users WHERE username = %s")
find_by_user_id_query = ("SELECT id, password FROM Users WHERE id = %s")
update_password_query = ("UPDATE Users SET password = %s WHERE id = %s")

def loginUser(username, password):
	cnx.start_transaction(isolation_level='READ COMMITTED')

	cursor = cnx.cursor()
	print("Now logging in user:", username, password)
	cursor.execute(query, (username.encode("utf-8"),))	
	result = cursor.fetchone()
	cnx.commit()

	if result is not None:
		id, hashed_password = result
		hashed_password_encoded = hashed_password.encode("utf-8")
		
		isValidPassword = bcrypt.hashpw(password.encode("utf-8"), hashed_password_encoded) == hashed_password_encoded

		if isValidPassword:
			return id
		else:
			return -1

	return -1


def updatePasssword(userId, old_password, new_password):
	cursor.execute(find_by_user_id_query, (userId,))

	for (id, stored_password) in cursor:
		stored_password = stored_password.encode("utf-8")

		if(bcrypt.checkpw(old_password.encode("utf-8"), stored_password)):

			user_data = (
				bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt()),
				userId
			)

			cursor.execute(update_password_query, user_data)
			cnx.commit()

			return "Password updated"

		else:
			return "Invalid password"



#print(updatePasssword("1", "admin", "admin"))