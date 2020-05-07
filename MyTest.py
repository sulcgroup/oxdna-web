import Database

def someFunctionIHopeWorks():

	connection = Database.pool.get_connection()

	results = None

	with connection.cursor() as cursor:
		# Read a single record
		sql = "SELECT * FROM Users"
		cursor.execute(sql)
		result = cursor.fetchall()
		results = result
		print(result)

	connection.close()

	return results

def sayHi():
	print("Hello there!")