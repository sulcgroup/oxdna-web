import os
import time
import uuid
import subprocess
import mysql.connector

cnx = mysql.connector.connect(user='root', password='', database='azdna')
cursor = cnx.cursor()

find_email_by_user_id_query = ("SELECT email FROM Users WHERE id = %s
set_email = ("UPDATE Users SET email = %s WHERE id = %s")
find_date_by_user_id_query = ("SELECT creationDate FROM Users WHERE id = %s")
find_status_by_user_id_query = ("SELECT status FROM Users WHERE id = %s")

def getEmail(userId):
	cursor.execute(find_email_by_user_id_query(userId))
	return cursor.email

def setEmail(email, userId):
	cursor.execute(set_email(email, userId)
	return "Email successfully updated!"

def getCreationDate(userId):
	cursor.execute(find_date_by_user_id_query(userId))
	return cursor.creationDate

def getStatus(userId):
	cursor.execute(find_status_by_user_id_query(userId))
	return cursor.status

