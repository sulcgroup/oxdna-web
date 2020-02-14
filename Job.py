import os
import time
import uuid
import subprocess
import mysql.connector

cnx = mysql.connector.connect(user='root', password='', database='azdna')
cursor = cnx.cursor()


add_job_query = (
	"INSERT INTO Jobs "
	"(`userId`, `name`, `uuid`, `slurmId`, `creationDate`)"
	"VALUES (%s, %s, %s, %s, %s)"
)

get_jobs_query = ("SELECT * FROM Jobs WHERE userId = %s")


def startSlurmJob(job_directory, job_id):
	sbatch_file = job_directory + "sbatch.sh"
	
	pipe = subprocess.Popen(["sbatch", sbatch_file], stdout=subprocess.PIPE)

	#trimming the last character to get rid of the trailing linebreak
	#the \n character
	output = pipe.communicate()[0].decode("ascii")[:-1]
	job_number = output.split("job ")[1]

	return job_number

def createSlurmJobFile(job_directory):
	#job_output_location = job_directory
	job_output_file = job_directory + "job_out.log"

	sbatch_file = """#!/bin/bash
#SBATCH --job-name=serial_job_test    # Job name
#SBATCH --ntasks=1                    # Run on a single CPU
#SBATCH --time=336:00:00               # Time limit hrs:min:sec
#SBATCH --output={job_output_file}   # Standard output and error log
cd {job_directory}
oxDNA input""".	format(
	job_directory=job_directory, 
	job_output_file=job_output_file
)
	
	file_name = "sbatch.sh"
	file_path = job_directory + file_name

	file = open(file_path, "w+")
	file.write(sbatch_file)

def createOxDNAFile(input_files, parameters, job_directory):
	input_file_data = ""

	for (file_name, _) in input_files.items():
		if(".top" in file_name):
			input_file_data += "topology = " + file_name + "\n"
		if(".dat" in file_name or ".conf" in file_name):
			input_file_data += "conf_file = " + file_name + "\n"

	for (key, value) in parameters.items():
		input_file_data += str(key) + " = " + str(value) + "\n"

	file_name = "input"
	file_path = job_directory + file_name

	file = open(file_path, "w+")
	file.write(input_file_data)
	file.close()

def createJobForUserIdWithData(userId, jsonData):

	randomJobId = str(uuid.uuid4())

	user_directory = "jobfiles/"+str(userId) + "/"
	job_directory = user_directory + randomJobId + "/"

	if not os.path.exists(user_directory):
		os.mkdir(user_directory)

	os.mkdir(job_directory)

	#pass randomJobId to slurm!
	files = jsonData["files"]

	#write the top and conf files
	for (file_name, file_data) in files.items():
		file_path = job_directory + file_name
		#print(file_directory)
		file = open(file_path, "w+")
		file.write(file_data)

	parameters = jsonData["parameters"]

	createOxDNAFile(files, parameters, job_directory)
	createSlurmJobFile(job_directory)
	
	job_number = startSlurmJob(job_directory, randomJobId)

	job_title = parameters["job_title"]

	job_data = (
		int(userId),
		job_title,
		randomJobId,
		job_number,
		int(time.time())
	)

	cursor.execute(add_job_query, job_data)
	cnx.commit()



def createJobDictionaryForTuple(data):

	job_id, user_id, job_name, uuid, slurm_id, creation_date = data

	schema = {
		"name":job_name,
		"uuid":uuid,
		"creationDate":creation_date
	}

	return schema


def getJobsForUserId(userId):
	
	cursor.execute(get_jobs_query, (int(userId),))
	result = cursor.fetchall()

	payload = []

	for data in result:
		job_data = createJobDictionaryForTuple(data)
		payload.append(job_data)


	return payload



'''
loldata = {
	"files": {
		"sim.top":"HELLO THIS IS A TOPOLOGY FILE",
		"test.conf":"THIS IS THE CONF FILE!!!:)"
	},
	"parameters": {
		"temperature":"100C"
	}
}
'''
#createJobForUserIdWithData(53, loldata)
#getJobsForUserId(12)
