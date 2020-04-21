from __future__ import print_function
from datetime import date, datetime, timedelta
import mysql.connector
import time
import bcrypt

query = ("SELECT id, password FROM Users WHERE username = %s")
find_by_user_id_query = ("SELECT id, password FROM Users WHERE id = %s")
update_password_query = ("UPDATE Users SET password = %s WHERE id = %s")
get_verified_query = ("SELECT verified FROM Users WHERE id = %s")

def loginUser(username, password):
	print("loggin in user")
	cnx = mysql.connector.connect(user='root', password='', database='azdna')
	cursor = cnx.cursor()

	cursor.execute(query, (username.encode("utf-8"),))

	for (id, hashed_password) in cursor.fetchall():
		hashed_password_encoded = hashed_password.encode("utf-8")

		isValidPassword = bcrypt.hashpw(password.encode("utf-8"), hashed_password_encoded) == hashed_password_encoded

		if isValidPassword:
			print("Password is valid")
			cursor.execute(get_verified_query, (id,))
			isVerified =  cursor.fetchall()
			if(isVerified):
				isVerified = isVerified[0][0]
			if isVerified == "True":
				return id
			else:
				return -2
		else:
			return -1

	cnx.close()

	return -1


def updatePasssword(userId, old_password, new_password):
	cnx = mysql.connector.connect(user='root', password='', database='azdna')
	cursor = cnx.cursor()

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
			cnx.close()

			return "Password updated"

		else:
			return "Invalid password"



#print(updatePasssword("1", "admin", "admin"))
