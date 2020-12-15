from __future__ import print_function
from datetime import date, datetime, timedelta
import time
import bcrypt

import Database
import Job

query = ("SELECT id, password, administrator FROM Users WHERE username = %s")
adminQuery = ("SELECT administrator FROM Users WHERE id = %s")
privalegedQuery = ("SELECT privaleged FROM Users WHERE id = %s")
recentUsersQuery = ("SELECT id, username FROM Users ORDER BY creationDate DESC LIMIT 5")
allUsersQuery = ("SELECT id, username FROM Users ORDER BY username ASC")
updateToAdministrator = ("UPDATE Users SET administrator = 1 WHERE id = %s")
updateToPrivaleged = ("UPDATE Users SET privaleged = 1 WHERE id = %s")
jobLimitQuery = ("SELECT jobLimit FROM Users WHERE id = %s")
jobCreationDateQuery = ("SELECT creationDate FROM Jobs WHERE uuid = %s")
timeLimitQuery = ("SELECT timeLimit FROM Users WHERE id = %s")
updateJobLimit = ("UPDATE Users SET jobLimit = %s WHERE id = %s")
setMonthlyTimeLimit = ("UPDATE Users SET timeLimit = %s WHERE id = %s")
userJobCountQuery = ("SELECT COUNT(*) FROM Jobs WHERE userId = %s")
userJobStatusCountQuery = ("SELECT COUNT(*) FROM Jobs WHERE userId = %s AND status = %s")
userIDQuery = ("SELECT id FROM Users WHERE username = %s")
remove_user = ("DELETE FROM Users WHERE id = %s")


def getRecentlyAddedUsers():
	result = []

	with Database.pool.get_connection() as connection:
		with connection.cursor() as cursor:
			cursor.execute(recentUsersQuery)
			result = cursor.fetchall()

	usernames = []

	for user_id, username in result:
		usernames.append(username)

	return usernames

def getAllUsers():
	result = []

	with Database.pool.get_connection() as connection:
		with connection.cursor() as cursor:
			cursor.execute(allUsersQuery)
			result = cursor.fetchall()

	usernames = []

	for user_id, username in result:
		usernames.append(username)

	return usernames

def checkIfAdmin(user_id):
	result = None

	with Database.pool.get_connection() as connection:
		with connection.cursor() as cursor:
			cursor.execute(adminQuery, (user_id,))
			result = cursor.fetchone()

	if result is not None:
		return result[0]
	else:
		return False

def checkIfPrivaleged(user_id):
	result = None
	with Database.pool.get_connection() as connection:
		with connection.cursor() as cursor:
			cursor.execute(privalegedQuery, (user_id,))
			result = cursor.fetchone()

	if result is not None:
		return result[0]
	else:
		return False

def promoteToAdmin(user_id):
	with Database.pool.get_connection() as connection:
		with connection.cursor() as cursor:
			cursor.execute(updateToAdministrator, (user_id,))

	connection.close()

def promoteToPrivaleged(user_id):
	with Database.pool.get_connection() as connection:
		with connection.cursor() as cursor:
			cursor.execute(updateToPrivaleged, (user_id,))

def getJobLimit(user_id):
	result = None

	with Database.pool.get_connection() as connection:
		with connection.cursor() as cursor:
			cursor.execute(jobLimitQuery, (user_id,))
			result = cursor.fetchone()

	if result is not None:
		return result[0]
	else:
		return 0

def getTimeLimit(user_id):
	result = None

	with Database.pool.get_connection() as connection:
		with connection.cursor() as cursor:
			cursor.execute(timeLimitQuery, (user_id,))
			result = cursor.fetchone()

	if result is not None:
		return result[0]
	else:
		return 0

def setJobLimit(user_id, jobs):
	with Database.pool.get_connection() as connection:
		with connection.cursor() as cursor:
			cursor.execute(updateJobLimit, (jobs, user_id,))

def setTimeLimit(user_id, timeLimit):
	with Database.pool.get_connection() as connection:
		with connection.cursor() as cursor:
			cursor.execute(setMonthlyTimeLimit, (timeLimit, user_id,))

def getUserJobCount(user_id):
	result = None

	with Database.pool.get_connection() as connection:
		with connection.cursor() as cursor:
			cursor.execute(userJobCountQuery, (user_id,))
			result = cursor.fetchone()

	if result is not None:
		return result[0]
	else:
		return 0

def getUserJobStatusCount(user_id, status):
	result = None

	with Database.pool.get_connection() as connection:
		with connection.cursor() as cursor:
			cursor.execute(userJobStatusCountQuery, (user_id, status,))
			result = cursor.fetchone()

	if result is not None:
		return result[0]
	else:
		return 0

def getUserActiveJobCount(user_id):
	return getUserJobStatusCount(user_id, "Pending") + getUserJobStatusCount(user_id, "Running") + getUserJobStatusCount(user_id, "Suspended") + getUserJobStatusCount(user_id, "Completing")

def deleteUser(user_id):
	try:
		Job.deleteJobsForUser(user_id)
	except:
		return "Couldn't delete user's job files"
	
	with Database.pool.get_connection() as connection:
		with connection.cursor() as cursor:
			cursor.execute(remove_user, (user_id))

	return "User has been deleted"

def getID(username):
	result = None

	with Database.pool.get_connection() as connection:
		with connection.cursor() as cursor:
			cursor.execute(userIDQuery, (username.encode("utf-8"),))
			result = cursor.fetchone()

	if result is not None:
		return result[0]
	else:
		return 0

#loginUser("david", "pass1234")