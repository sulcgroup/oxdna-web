from __future__ import print_function
from datetime import date, datetime, timedelta
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

	result = None

	with connection.cursor() as cursor:
		cursor.execute(query, (username,))
		result = cursor.fetchone()

	if result is not None:
		user_id, password_hash, verified = result

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

	connection = Database.pool.get_connection()

	result = None

	with connection.cursor() as cursor:
		cursor.execute(find_by_user_id_query, (userId,))
		result = cursor.fetchone()

	if result is None:
		return "There was an error with your account"

	user_id, stored_password = result

	password_check = bcrypt.checkpw(old_password.encode("utf8"), stored_password.encode("utf8"))

	user_data = (
		bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt()),
		userId
	)

	if password_check:
		with connection.cursor() as cursor:
			cursor.execute(update_password_query, user_data)

	connection.close()

	if password_check:
		return "Password updated"
	else:
		return "Incorrect password"
