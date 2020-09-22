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

defaultJobLimit = 4
add_user_query = (
"INSERT INTO Users"
"(`username`, `password`, `group`, `creationDate`, `verifycode`, `verified`, `firstName`, `lastName`, `institution`, `jobLimit`)"
"VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
)
group_query = ("SELECT `group` FROM Users WHERE username = %s")

def registerUser(user, requires_verification=True):
	connection = Database.pool.get_connection()

	response = validate(user)
	print(response)
	if len(response) > 0:
		connection.close()
		return response
	
	name = user["email"]
	firstName = user["firstName"]
	lastName = user["lastName"]
	institution = user["institution"]
	password = user["password"]

	verifycode = binascii.b2a_hex(os.urandom(15)).decode("utf-8")
	user_data = (name, bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()), 0, int(time.time()), verifycode, "False", firstName, lastName, institution, defaultJobLimit)

	if requires_verification == False:
		user_data = (name, bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()), 0, int(time.time()), verifycode, "True", firstName, lastName, institution, defaultJobLimit)

	with connection.cursor() as cursor:
		cursor.execute(add_user_query, user_data)

	user_id = Account.getUserId(name)

	if requires_verification:
		verifylink = "http://oxdna.org/verify?id={userId}&verify={verifycode}".format(userId = user_id, verifycode = verifycode)
		EmailScript.SendEmail("-t 0 -n {username} -u {verifylink} -d {email}".format(username = name, verifylink = verifylink, email = name).split(" "))

	connection.close()
	return "Success"

def validate(user):
	errors = {}

	if "firstName" not in user:
		errors["firstName"] = "Empty field"
	if "lastName" not in user:
		errors["lastName"] = "Empty field"
	if "institution" not in user:
		errors["institution"] = "Empty field"
	if "email" not in user:
		errors[""] = "Empty field"
	else:
		if "@" not in user["email"]:
			errors["email"] = "Invalid email"
		elif Account.getUserId(user["email"]):
			errors["email"] = "Email is already registered"
	if "password" not in user or len(user["password"]) < 8:
		errors["password"] = "Must be at least 8 characters"

	return errors

def getGroup(email):
	connection = Database.pool.get_connection()
	result = None
	
	with connection.cursor() as cursor:
		cursor.execute(group_query, (email))
		result = cursor.fetchone()[0]

	connection.close()
	return result if result else None

def registerGuest(email):
	connection = Database.pool.get_connection()
	user_id = Account.getUserId(email)
	if user_id:
		return "Guest exists" if getGroup(email) == 1 else "User exists"
	
	name = email
	firstName = "Guest"
	lastName = "Guest"
	institution = "Guest"
	password = "Guest"
	verifycode = "Guest"

	user_data = (name, bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()), 1, int(time.time()), verifycode, "False", firstName, lastName, institution, defaultJobLimit)

	connection.cursor().execute(add_user_query, user_data)

	connection.close()
	return "Success"