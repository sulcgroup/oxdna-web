import os
import time
import uuid
import subprocess
import mysql.connector


cnx = mysql.connector.connect(user='root', password='', database='azdna')

set_analysis_id_query = (
	"UPDATE Jobs SET analysisJobId = %s WHERE uuid = %s"
)

add_job_query = (
	"INSERT INTO Jobs "
	"(`userId`, `name`, `uuid`, `slurmId`, `jobType`, `analysisJobId`, `creationDate`)"
	"VALUES (%s, %s, %s, %s, %s, %s, %s)"
)

get_jobs_query = ("SELECT * FROM Jobs WHERE userId = %s")
get_job_query = ("SELECT * FROM Jobs WHERE uuid = %s")


def startSlurmJob(job_directory, job_id):
	sbatch_file = job_directory + "sbatch.sh"
	
	pipe = subprocess.Popen(["sbatch", sbatch_file], stdout=subprocess.PIPE)

	#trimming the last character to get rid of the trailing linebreak
	#the \n character
	output = pipe.communicate()[0].decode("ascii")[:-1]
	job_number = output.split("job ")[1]

	return job_number

def startSlurmAnalysis(job_directory):
	sbatch_file = job_directory + "sbatch_analysis.sh"
	
	pipe = subprocess.Popen(["sbatch", sbatch_file], stdout=subprocess.PIPE)

	output = pipe.communicate()[0].decode("ascii")[:-1]
	job_number = output.split("job ")[1]

	return job_number

def createSlurmAnalysisFile(job_directory, analysis_id):
	job_output_file = job_directory + "analysis_out.log"


	sbatch_file = """#!/bin/bash
#SBATCH --job-name={analysis_id}    # Job name
#SBATCH --ntasks=1                    # Run on a single CPU
#SBATCH --time=336:00:00               # Time limit hrs:min:sec
#SBATCH --output=/vagrant/azDNA/{job_output_file}   # Standard output and error log
cd /vagrant/azDNA/{job_directory}
python3 /vagrant/oxdna_analysis_tools/compute_mean.py -p 1 -d deviations.json -f oxDNA -o mean.dat trajectory.dat sim.top""".format(
	analysis_id=analysis_id,
	job_directory=job_directory, 
	job_output_file=job_output_file
)

	file_name = "sbatch_analysis.sh"
	file_path = job_directory + file_name


	file = open(file_path, "w+")
	file.write(sbatch_file)
	

def createSlurmJobFile(job_directory):
	#job_output_location = job_directory
	job_output_file = job_directory + "job_out.log"

	sbatch_file = """#!/bin/bash
#SBATCH --job-name=serial_job_test    # Job name
#SBATCH --ntasks=1                    # Run on a single CPU
#SBATCH --time=336:00:00               # Time limit hrs:min:sec
#SBATCH --output=/vagrant/azDNA/{job_output_file}   # Standard output and error log
cd /vagrant/azDNA/{job_directory}
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

def createAnalysisForUserIdWithJob(userId, jobId):
	cursor = cnx.cursor(buffered=True)

	randomAnalysisId = str(uuid.uuid4())

	user_directory = "jobfiles/"+str(userId) + "/"
	job_directory = user_directory + jobId + "/"

	createSlurmAnalysisFile(job_directory, randomAnalysisId)
	job_number = startSlurmAnalysis(job_directory)

	print("Creating analysis now...")

	update_data = (
		randomAnalysisId,
		jobId
	)

	cursor.execute(set_analysis_id_query, update_data)
	cnx.commit()

	analysis_data = (
		int(userId),
		"analysis",
		randomAnalysisId,
		job_number,
		1,
		None,
		int(time.time())
	)
	cursor.execute(add_job_query, analysis_data)
	cnx.commit()
	cursor.close()

	return randomAnalysisId


def createJobForUserIdWithData(userId, jsonData):
	cursor = cnx.cursor(buffered=True)
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
		0,
		None,
		int(time.time())
	)

	cursor.execute(add_job_query, job_data)
	cnx.commit()
	cursor.close()



def createJobDictionaryForTuple(data):

	job_id, user_id, job_name, uuid, slurm_id, job_type, analysis_job_id, creation_date = data

	schema = {
		"name":job_name,
		"uuid":uuid,
		"job_type":job_type,
		"analysisJobId":analysis_job_id,
		"creationDate":creation_date,
	}

	return schema


def getJobsForUserId(userId):

	temp_cnx = mysql.connector.connect(user='root', password='', database='azdna')
	cursor = temp_cnx.cursor(buffered=True)

	
	cursor.execute(get_jobs_query, (int(userId),))
	result = cursor.fetchall()

	payload = []

	for data in result:
		job_data = createJobDictionaryForTuple(data)
		payload.append(job_data)


	cursor.close()
	temp_cnx.close()
	return payload


def getJobForUserId(jobId, userId):
	temp_cnx = mysql.connector.connect(user='root', password='', database='azdna')

	cursor = temp_cnx.cursor(buffered=True)
	cursor.execute(get_job_query, (jobId,))
	result = cursor.fetchone()

	cursor.close()
	temp_cnx.close()
	if(result is not None):
		return createJobDictionaryForTuple(result)
	else:
		return None



#createJobForUserIdWithData(53, loldata)
#getJobsForUserId(12)
#createAnalysisForUserIdWithJob(1, "72a302e1-0efe-40ef-804e-dbffb4842b41")
#getJobForUserId("72a302e1-0efe-40ef-804e-dbffb4842b41", 1)