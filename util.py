from __future__ import print_function
from datetime import date, datetime, timedelta
import time
import bcrypt



def log_output(text):
	output_file = open("output.txt", "a")
	print(text, file=output_file)
	output_file.close()

#loginUser("david", "pass1234")