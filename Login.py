from __future__ import print_function
from datetime import date, datetime, timedelta
import mysql.connector
import time
import bcrypt

cnx = mysql.connector.connect(user='root', password='', database='azdna')
cursor = cnx.cursor()

query = ("SELECT id, password FROM Users WHERE username = %s")

def loginUser(username, password):
	cursor.execute(query, (username.encode("utf-8"),))	

	for (id, hashed_password) in cursor:
		hashed_password_encoded = hashed_password.encode("utf-8")
		
		isValidPassword = bcrypt.hashpw(password.encode("utf-8"), hashed_password_encoded) == hashed_password_encoded

		if isValidPassword:
			return id
		else:
			return -1

	return -1


#loginUser("david", "pass1234")