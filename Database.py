import pymysql
import pymysqlpool

pymysqlpool.logger.setLevel('DEBUG')
config = {'host':'localhost', 'user':'root', 'password':'', 'database':'azdna', 'autocommit':True}
pool = pymysqlpool.ConnectionPool(size=4, name='pool1', **config)