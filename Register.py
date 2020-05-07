from __future__ import print_function
from datetime import date, datetime, timedelta
import time
import Login
import Account
import bcrypt
import os
import binascii
import EmailScript

import Database

add_user_query = (
"INSERT INTO Users"
"(`username`, `password`, `group`, `creationDate`, `verifycode`, `verified`, `firstName`, `lastName`, `institution`)"
"VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
)

#needs input cleaning/escaping/validation

def registerUser(name, password, firstName, lastName, institution, requires_verification=True):
	connection = Database.pool.get_connection()
	
	#check if the user already exists.
	if Account.getUserId(name):
		connection.close()
		return -2 #value that is not none means user is in the database. return -2 error code.

	verifycode = binascii.b2a_hex(os.urandom(15)).decode("utf-8")
	user_data = (name, bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()), 0, int(time.time()), verifycode, "False", firstName, lastName, institution)

	if requires_verification == False:
		user_data = (name, bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()), 0, int(time.time()), verifycode, "True", firstName, lastName, institution)

	with connection.cursor() as cursor:
		cursor.execute(add_user_query, user_data)

	user_id = Account.getUserId(name)

	if requires_verification:
		verifylink = "http://10.126.22.10/verify?id={userId}&verify={verifycode}".format(userId = user_id, verifycode = verifycode)
		EmailScript.SendEmail("-t 0 -n {username} -u {verifylink} -d {email}".format(username = name, verifylink = verifylink, email = name).split(" "))

	connection.close()
	return user_id



