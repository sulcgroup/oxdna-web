<p align="center">
<img src="https://user-images.githubusercontent.com/3137957/87845100-0f35bf00-c879-11ea-8d57-bb7411f0ae6a.png">
</p>
# oxDNA.org

Welcome to oxdna.org, this is a repository for running a user-friendly oxDNA webserver. 

Note, you are free to run the server as-is, by cloning and running main.py, but it is available as a packaged Vagrant virtualbox, allowing you to easily setup a proper environment with all necessary libraries and software (MySQL, Flask, Slurm, etc...). The environment can be seen here: https://github.com/rjro/azDNA_env

## Guidelines

This project uses Python modules to separate functionality and logic. The "Jobs" module in Jobs.py handles the creation and management of jobs, and the "Accounts" module in Accounts.py handles the creation and management of accounts. Please follow this design pattern.

The main entry-point of the application, where all the routes are defined, can be found in main.py.

> When interfacing with the MySQL database, ensure that you handle and close your connections properly. See the section [Interfacing with the Database](#Interfacing-with-the-Database).below for more information.

## Running as a Production Server

If you invoke "python3 [main.py](main.py)" you will be running the development version of the Flask webserver, but it is not suitable for production, is not stable and does not scale. 

To run a proper production server, you will need to use [gunicorn](https://pypi.org/project/gunicorn/).

You must then comment out the "app.run()" call from main.py, create a new file (called wsgi.py), and add the following code:

**This functionality will soon be integrated into this repository by default**

```python
from main import app

if __name__ == "__main__":
    app.run()
```
You then start gunicorn from the command line with:

```
gunicorn --bind 0.0.0.0:9000 wsgi:app --workers=3
```
## Interfacing with the Database

This application makes use of the [pymysql](https://pypi.org/project/PyMySQL/) and [pymysql-pool](https://pypi.org/project/pymysql-pool/) libraries for interfacing with MySQL.

You can see how this interface is configured within the [Database](Database.py) module. Ten connections are created for interfacing with the MySQL database, these connections are then stored in a pool and re-used throughout  the lifecycle of the application.

In order to use a connection, use the following procedure:
```python
import Database

connection = Database.pool.get_connection()
results = None

with connection.cursor() as cursor:
	cursor.execute("SELECT * FROM Users")
	results = cursor.fetchall()

#Remember this!
connection.close()
```

Please be sure to close your connection, or else the server will crash if it exhausts the connection pool.
