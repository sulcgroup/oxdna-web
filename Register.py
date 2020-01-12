from __future__ import print_function
from datetime import date, datetime, timedelta
import mysql.connector
import time
import Login
import bcrypt

cnx = mysql.connector.connect(user='root', password='', database='azdna')
cursor = cnx.cursor()


add_user_query = (
	"INSERT INTO Users "
	"(`username`, `password`, `group`, `creationDate`)"
	"VALUES (%s, %s, %s, %s)"
)

#needs input cleaning/escaping/validation
#throws no errors atm if user already exists
def registerUser(name, password):

	user_data = (name, bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()), 0, int(time.time()))
	cursor.execute(add_user_query, user_data)
	cnx.commit()

	user_id = Login.loginUser(name, password)

	return user_id

'''
import random
letters = "abcdefghijklmnopqrstuvwxyz"
random_name = "".join([random.choice(letters) for _ in range(5)])
registerUser(random_name, "pass123")
'''