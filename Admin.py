from __future__ import print_function
from datetime import date, datetime, timedelta
import mysql.connector
import time
import bcrypt



cnx = mysql.connector.connect(user='root', password='', database='azdna')
cursor = cnx.cursor()

query = ("SELECT id, password, administrator FROM Users WHERE username = %s")
adminQuery = ("SELECT administrator FROM Users WHERE id = %s")
privalegedQuery = ("SELECT privaleged FROM Users WHERE id = %s")
recentUsersQuery = ("SELECT id, username FROM Users ORDER BY creationDate DESC LIMIT 5")
updateToAdministrator = ("UPDATE Users SET administrator = 1 WHERE id = %s")
updateToPrivaleged = ("UPDATE Users SET privaleged = 1 WHERE id = %s")
userJobCountQuery = ("SELECT COUNT(*) FROM Jobs WHERE userId = %s")
userIDQuery = ("SELECT id FROM Users WHERE username = %s")



def getRecentlyAddedUsers():
	cursor.execute(recentUsersQuery)

	newUsers = []
	for (id, username) in cursor:
		newUsers.append(username)
	return newUsers

def checkIfAdmin(uuid):
	cursor.execute(adminQuery, (uuid,))
	for (admin) in cursor:
		return admin[0]

def checkIfPrivaleged(uuid):
	cursor.execute(privalegedQuery, (uuid,))
	for (priv) in cursor:
		return priv[0]

def promoteToAdmin(uuid):
	cursor.execute(updateToAdministrator, (uuid,))
	cnx.commit()

def promoteToPrivaleged(uuid):
	cursor.execute(updateToPrivaleged, (uuid,))
	cnx.commit()

def getUserJobCount(uuid):
	cursor.execute(userJobCountQuery, (uuid,))
	for (count) in cursor:
		return count[0]

def getID(username):
	print(username)
	cursor.execute(userIDQuery, (username.encode("utf-8"),))
	for (id) in cursor:
		print(id)
		return id[0]
	return 0

#loginUser("david", "pass1234")