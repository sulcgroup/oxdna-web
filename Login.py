from __future__ import print_function
from datetime import date, datetime, timedelta
import mysql.connector
import time
import bcrypt


import Database

query = ("SELECT id, password, verified FROM Users WHERE username = %s")
find_by_user_id_query = ("SELECT id, password FROM Users WHERE id = %s")
update_password_query = ("UPDATE Users SET password = %s WHERE id = %s")
get_verified_query = ("SELECT verified FROM Users WHERE id = %s")

def loginUser(username, password):

	print("Now logging in user:", username)

	connection = Database.pool.get_connection()

	user_id, password_hash, verified = None, None, None
	verification_status = None

	with connection.cursor() as cursor:
		cursor.execute(query, (username,))
		#res = cursor.fetchone()
		user_id, password_hash, verified = cursor.fetchone()

	if user_id is None or password_hash is None:
		connection.close()
		return -1

	with connection.cursor() as cursor:
		cursor.execute(get_verified_query, (user_id,))
		res = cursor.fetchone()
		
	connection.close()

	password_check = bcrypt.checkpw(password.encode("utf8"), password_hash.encode("utf8"))

	if password_check:
		if verified == "True":
			return user_id
		else:
			return -2


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

