import os
import time
import uuid
import subprocess
import mysql.connector

import Database

find_email_by_user_id_query = ("SELECT email FROM Users WHERE id = %s")
set_email = ("UPDATE Users SET email = %s WHERE id = %s")
find_date_by_user_id_query = ("SELECT creationDate FROM Users WHERE id = %s")
find_status_by_user_id_query = ("SELECT status FROM Users WHERE id = %s")
get_verify_code_query = ("SELECT verifycode FROM Users WHERE id = %s")
verify_user = ("UPDATE Users SET verified = %s WHERE id = %s")
get_username_query = ("SELECT username FROM Users WHERE id = %s")
get_userid_query = ("SELECT id FROM Users WHERE username = %s")


##DEPRECATED
def getEmail(userId):
	connection = Database.pool.get_connection()
	result = None

	with connection.cursor() as cursor:
		cursor.execute(find_email_by_user_id_query, userId)
		result = cursor.fetchone()

	connection.close()
	return result[0]

def setEmail(email, userId):
	connection = Database.pool.get_connection()

	with connection.cursor() as cursor:
		cursor.execute(set_email, (email, userId))
	
	connection.close()
	return "Email successfully updated!"
##DEPRECATED

def getCreationDate(userId):
	connection = Database.pool.get_connection()
	results = None

	with connection.cursor() as cursor:
		cursor.execute(find_date_by_user_id_query, (userId,))
		#fetchall returns all results
		results = cursor.fetchall()
	
	connection.close()

	if results is not None:
		return results[0][0]
	else:
		return None

def getStatus(userId):

	connection = Database.pool.get_connection()
	results = None

	with connection.cursor() as cursor:
		cursor.execute(find_status_by_user_id_query, (userId,))
		#fetchall returns all results
		results = cursor.fetchall()

	connection.close()

	if results is not None:
		return results[0][0]
	else:
		return None

def getVerificationCode(userId):
	connection = Database.pool.get_connection()
	results = None

	with connection.cursor() as cursor:
		cursor.execute(get_verify_code_query, (userId,))
		results = cursor.fetchall()

	if results is not None:
		return results[0][0]
	else:
		return None

def getUsername(userId):
	connection = Database.pool.get_connection()
	results = None

	with connection.cursor() as cursor:
		cursor.execute(get_username_query, (userId,))
		results = cursor.fetchall()

	if results is not None:
		return results[0][0]
	else:
		return None

def getUserId(username):
	connection = Database.pool.get_connection()
	results = None

	with connection.cursor() as cursor:
		cursor.execute(get_userid_query, (username,))
		results = cursor.fetchall()

	connection.close()

	if results is not None:
		return results[0][0]
	else:
		return None


#checks verification code for user
def verifyUser(userId, VerifyCode):
	connection = Database.pool.get_connection()

	code = None
	with connection.cursor() as cursor:
		cursor.execute(get_verify_code_query, (userId,))
		code = cursor.fetchall()

	if code is not None and code[0][0] == VerifyCode:
		with connection.cursor() as cursor:
			cursor.execute(verify_user, ("True", userId))
		return True
	
	return False