import os
import time
import uuid
import subprocess
import bcrypt
import EmailScript

import Database

find_email_by_user_id_query = ("SELECT email FROM Users WHERE id = %s")
set_email = ("UPDATE Users SET email = %s WHERE id = %s")
find_date_by_user_id_query = ("SELECT creationDate FROM Users WHERE id = %s")
find_status_by_user_id_query = ("SELECT status FROM Users WHERE id = %s")
get_verify_code_query = ("SELECT verifycode FROM Users WHERE id = %s")
verify_user = ("UPDATE Users SET verified = %s WHERE id = %s")
get_username_query = ("SELECT username FROM Users WHERE id = %s")
get_userid_query = ("SELECT id FROM Users WHERE username = %s")
set_reset_token = ("UPDATE Users SET resetToken = %s WHERE username = %s")
check_reset_token = ("SELECT id FROM Users WHERE resetToken = %s")
reset_password = ("UPDATE Users SET password = %s WHERE id = %s")
set_reset_token_expiration = ("UPDATE Users SET resetTokenExpiration = %s WHERE username = %s")
get_reset_token_expiration = ("SELECT resetTokenExpiration FROM Users WHERE id = %s")



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

	connection.close()

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

	connection.close()

	if results is not None:
		return results[0][0]
	else:
		return None

def getUserId(username):
	connection = Database.pool.get_connection()
	
	result = None

	with connection.cursor() as cursor:
		cursor.execute(get_userid_query, (username,))
		result = cursor.fetchone()

	connection.close()

	if result is not None:
		return result[0]
	else:
		return None


#checks verification code for user
def verifyUser(userId, VerifyCode):
	connection = Database.pool.get_connection()

	code = None
	with connection.cursor() as cursor:
		cursor.execute(get_verify_code_query, (userId,))
		code = cursor.fetchall()

	connection.close()

	if code is not None and code[0][0] == VerifyCode:
		with connection.cursor() as cursor:
			cursor.execute(verify_user, ("True", userId))
		return True
	
	return False

def sendResetToken(username):
	connection = Database.pool.get_connection()
	token = str(uuid.uuid4())
	day = time.time() + 86400

	with connection.cursor() as cursor:
		cursor.execute(set_reset_token, (token, username,))
		cursor.execute(set_reset_token_expiration, (day, username,))
	
	### UPDATE LINK WHEN DOMAIN GOES PUBLIC ###
	verifylink = "http://localhost:9000/password/reset?token={token}".format(token = token)
	EmailScript.SendEmail("-t 6 -n {username} -u {verifylink} -d {email}".format(username = username, verifylink = verifylink, email = username).split(" "))

	connection.close()
	return "Email sent"

def checkToken(token):
	connection = Database.pool.get_connection()
	userId = 0
	expirationTime = 0

	with connection.cursor() as cursor:
		cursor.execute(check_reset_token, (token,))
		userId = cursor.fetchone()

	if not userId:
		connection.close()
		return 0
	
	with connection.cursor() as cursor:
		cursor.execute(get_reset_token_expiration, userId[0])
		expirationTime = cursor.fetchone()
	
	if time.time() > expirationTime[0]:
		connection.close()
		return -1
	else:
		connection.close()
		return userId[0]


def resetPassword(userId, newPassword):
	connection = Database.pool.get_connection()
	user_data = (
		bcrypt.hashpw(newPassword.encode("utf-8"), bcrypt.gensalt()),
		userId
	)

	with connection.cursor() as cursor:
		cursor.execute(reset_password, user_data)

	connection.close()
	return "Password succesfully changed!"
