import os
import time
import uuid
import subprocess
import bcrypt
import EmailScript

import Database

get_email_prefs = ("SELECT emailPrefs FROM Users WHERE id = %s")
set_email_prefs = ("UPDATE Users SET emailPrefs = %s WHERE id = %s")
find_email_by_user_id_query = ("SELECT username FROM Users WHERE id = %s")
set_email = ("UPDATE Users SET username = %s WHERE id = %s")
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
get_name_by_id_query = ("SELECT firstName FROM Users WHERE id = %s")

def getEmailPrefs(userId):
	result = None
	with Database.pool.get_connection() as connection:
		with connection.cursor() as cursor:
			cursor.execute(get_email_prefs, userId)
			result = cursor.fetchone()[0]

	return result

def setEmailPrefs(userId, prefs):
	print(prefs)
	print(type(prefs))
	print(prefs[0])

	prefs_integers = list(map(lambda x: "1" if x == "true" else "0", prefs.split(",")))
	result = " ".join(prefs_integers)

	with Database.pool.get_connection() as connection:
		with connection.cursor() as cursor:
			cursor.execute(set_email_prefs, (result, userId))

	return "Success"

##DEPRECATED
def getEmail(userId):
	result = None

	with Database.pool.get_connection() as connection:
		with connection.cursor() as cursor:
			cursor.execute(find_email_by_user_id_query, userId)
			result = cursor.fetchone()

	return result[0]

def setEmail(email, userId):
	with Database.pool.get_connection() as connection:
		with connection.cursor() as cursor:
			cursor.execute(set_email, (email, userId))

	return "Email successfully updated!"
##DEPRECATED

def getCreationDate(userId):
	results = None

	with Database.pool.get_connection() as connection:
		with connection.cursor() as cursor:
			cursor.execute(find_date_by_user_id_query, (userId,))
			#fetchall returns all results
			results = cursor.fetchall()

	if results is not None:
		return results[0][0]
	else:
		return None

def getStatus(userId):
	results = None

	with Database.pool.get_connection() as connection:
		with connection.cursor() as cursor:
			cursor.execute(find_status_by_user_id_query, (userId,))
			#fetchall returns all results
			results = cursor.fetchall()

	if results is not None:
		return results[0][0]
	else:
		return None

def getVerificationCode(userId):
	results = None
	with Database.pool.get_connection() as connection:
		with connection.cursor() as cursor:
			cursor.execute(get_verify_code_query, (userId,))
			results = cursor.fetchall()

	if results is not None:
		return results[0][0]
	else:
		return None

def getUsername(userId):
	results = None

	with Database.pool.get_connection() as connection:
		with connection.cursor() as cursor:
			cursor.execute(get_username_query, (userId,))
			results = cursor.fetchall()

	if results is not None:
		print(results)
		return results[0][0]
	else:
		return None

def getUserId(username):
	result = None

	with Database.pool.get_connection() as connection:
		with connection.cursor() as cursor:
			cursor.execute(get_userid_query, (username,))
			result = cursor.fetchone()

	if result is not None:
		return result[0]
	else:
		return None


#checks verification code for user
def verifyUser(userId, VerifyCode):
	code = None
	with Database.pool.get_connection() as connection:
		with connection.cursor() as cursor:
			cursor.execute(get_verify_code_query, (userId,))
			code = cursor.fetchall()

	if code is not None and code[0][0] == VerifyCode:
		with connection.cursor() as cursor:
			cursor.execute(verify_user, ("True", userId))
		return True
	
	return False

def sendResetToken(username):
	token = str(uuid.uuid4())
	day = time.time() + 86400

	with Database.pool.get_connection() as connection:
		with connection.cursor() as cursor:
			cursor.execute(set_reset_token, (token, username,))
			cursor.execute(set_reset_token_expiration, (day, username,))
	
	verifylink = "http://oxdna.org/password/reset?token={token}".format(token = token)
	EmailScript.SendEmail("-t 6 -n {username} -u {verifylink} -d {email}".format(username = username, verifylink = verifylink, email = username).split(" "))

	return "Email sent"

def checkToken(token):
	userId = 0
	expirationTime = 0

	with Database.pool.get_connection() as connection:
		with connection.cursor() as cursor:
			cursor.execute(check_reset_token, (token,))
			userId = cursor.fetchone()

		if not userId:
			return 0
	
		with connection.cursor() as cursor:
			cursor.execute(get_reset_token_expiration, userId[0])
			expirationTime = cursor.fetchone()
	
		if time.time() > expirationTime[0]:
			return -1

	return userId[0]


def resetPassword(userId, newPassword):
	user_data = (
		bcrypt.hashpw(newPassword.encode("utf-8"), bcrypt.gensalt()),
		userId
	)

	with Database.pool.get_connection() as connection:
		with connection.cursor() as cursor:
			cursor.execute(reset_password, user_data)

	return "Password succesfully changed!"

def getFirstName(userId):
	with Database.pool.get_connection() as connection:
		with connection.cursor() as cursor:
			cursor.execute(get_name_by_id_query, userId)
			name = cursor.fetchone()[0]
			
	return name
