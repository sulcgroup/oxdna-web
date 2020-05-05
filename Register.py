from __future__ import print_function
from datetime import date, datetime, timedelta
import mysql.connector
import time
import Login
import Account
import bcrypt
import os
import binascii
import EmailScript

add_user_query = (
"INSERT INTO Users"
"(`username`, `password`, `group`, `creationDate`, `verifycode`, `verified`, `firstName`, `lastName`, `institution`)"
"VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
)

#needs input cleaning/escaping/validation

def registerUser(name, password, firstName, lastName, institution, requires_verification=True):
	cnx = mysql.connector.connect(user='root', password='', database='azdna')
	cursor = cnx.cursor()
	
	#check if the user already exists.
	if(Account.getUserId(name)):
		cnx.close()
		return -2 #value that is not none means user is in the database. return -2 error code.

	verifycode = binascii.b2a_hex(os.urandom(15)).decode("utf-8")
	user_data = (name, bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()), 0, int(time.time()), verifycode, "False", firstName, lastName, institution)

	if requires_verification == False:
		user_data = (name, bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()), 0, int(time.time()), verifycode, "True", firstName, lastName, institution)
		

	cursor.execute(add_user_query, user_data)
	cnx.commit()

	user_id = Account.getUserId(name)

	if requires_verification:
		verifylink = "http://10.126.22.10/verify?id={userId}&verify={verifycode}".format(userId = user_id, verifycode = verifycode)
		EmailScript.SendEmail("-t 0 -n {username} -u {verifylink} -d {email}".format(username = name, verifylink = verifylink, email = name).split(" "))

	cnx.close()
	return user_id


'''
import random
letters = "abcdefghijklmnopqrstuvwxyz"
random_name = "".join([random.choice(letters) for _ in range(5)])
registerUser(random_name, "pass123")
'''
