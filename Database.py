import pymysql
import pymysqlpool
import inspect
import uuid

class MyConnection:
	def __init__(self, connection, opener, identifier):
		self.identifier = identifier
		self.opener = opener
		self.closer = None
		self._connection = connection

	def __enter__(self):
		return self
		
	def __exit__(self, exc_type, exc_value, exc_traceback):
		if (exc_type or exc_value or exc_traceback):
			print("There was an error in a database call!:\nexc_type: {}\nexc_value: {}\nexc_traceback: {}\n".format(exc_type, exc_value, exc_traceback))
		self.close()

	def close(self):
		curframe = inspect.currentframe()
		calframe = inspect.getouterframes(curframe, 2)

		function_caller = calframe[1][3]

		self.closer = function_caller
		self._connection.close()
		#print("CONNECTION: ", self.identifier, " CLOSE BY:", function_caller, flush=True)

	def cursor(self):
		return self._connection.cursor()

class MyPool:
	def __init__(self):
		pymysqlpool.logger.setLevel('DEBUG')
		config = {'host':'localhost', 'user':'root', 'password':'', 'database':'azdna', 'autocommit':True}
		self._pool = pymysqlpool.ConnectionPool(size=10, name='pool1', **config)
	
	def get_connection(self):
		#https://stackoverflow.com/questions/2654113/how-to-get-the-callers-method-name-in-the-called-method
		curframe = inspect.currentframe()
		calframe = inspect.getouterframes(curframe, 2)

		function_caller = calframe[1][3]
		connection_identifier = str(uuid.uuid4())[:5]

		#print("CONNECTION: ", connection_identifier, " OPEN BY:", calframe[1][3])

		wrapped_connection = MyConnection(self._pool.get_connection(), function_caller, connection_identifier)

		return wrapped_connection


pool = MyPool()