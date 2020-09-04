import os
from time import time
from Database import pool
from Job import getJobNameForUuid
from Account import getUsername
from Admin import getTimeLimit
from EmailScript import SendEmail

# This script is called at the end of sbatch.sh
# It updates the job status and user's time limit in SQL

current_time = time()
path = os.getcwd().split('/')
user_id = path[2]
job_uuid = path[3]

connection = pool.get_connection()

# update job status
with connection.cursor() as cursor:
    cursor.execute("UPDATE Jobs SET status = \"Completed\" WHERE uuid = %s", (job_uuid))

# compute new time limit
with connection.cursor() as cursor:
    cursor.execute("SELECT creationDate FROM Jobs WHERE uuid = %s", (job_uuid,))
    creation_time = int(cursor.fetchone()[0])

elapsed_time = current_time - creation_time
new_time_limit = getTimeLimit(user_id) - elapsed_time
if new_time_limit < 0:
    new_time_limit = 0

# update time limit
with connection.cursor() as cursor:
    cursor.execute("UPDATE Users SET timeLimit = %s WHERE id = %s", (new_time_limit, user_id))
connection.close()

print("Remaining monthly time limit: ", str(new_time_limit), " seconds")

# email user about job completion
username = getUsername(user_id)
jobname = getJobNameForUuid(job_uuid)
link = "https://oxdna.org/job/" + job_uuid
SendEmail("-t 7 -n {username} -j {jobname} -u {link} -d {email}".format(username = username, jobname = jobname, link = link, email = username).split(" "))
