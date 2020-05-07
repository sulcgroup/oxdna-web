import os
import time
import uuid
import subprocess


import mysql.connector


import Database



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
get_userId_for_job_uuid = ("SELECT userID FROM Jobs WHERE uuid = %s")
remove_job = ("DELETE FROM Jobs WHERE uuid = %s")
get_status = ("SELECT status FROM Jobs WHERE uuid = %s")
update_status = ("UPDATE Jobs SET status = %s WHERE uuid = %s")


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
#SBATCH --partition=CPU
#SBATCH --ntasks=1                    # Run on a single CPU
#SBATCH --time=100:00:00               # Time limit hrs:min:sec
#SBATCH --output={job_output_file}   # Standard output and error log
cd {job_directory}
python3 /opt/oxdna_analysis_tools/compute_mean.py -p 1 -d deviations.json -f oxDNA -o mean.dat trajectory.dat output.top""".format(
	analysis_id=analysis_id,
	job_directory=job_directory, 
	job_output_file=job_output_file
)

	file_name = "sbatch_analysis.sh"
	file_path = job_directory + file_name


	print("Creating analysis file at filepath:", file_path)

	file = open(file_path, "w+")
	file.write(sbatch_file)

def createSlurmJobFile(job_directory, job_name, backend, input_files):
	#job_output_location = job_directory
	job_output_file = job_directory + "job_out.log"
	if backend == "CPU":
		sbatch_file = """#!/bin/bash
#SBATCH --job-name={job_name}    # Job name
#SBATCH --partition={backend}
#SBATCH --ntasks=1                    # Run on a single CPU
#SBATCH --time=100:00:00               # Time limit hrs:min:sec
#SBATCH --output={job_output_file}   # Standard output and error log
cd {job_directory}""".	format(
	job_directory=job_directory, 
	job_output_file=job_output_file,
	backend=backend,
	job_name=job_name
	)
	
	else:
		sbatch_file = """#!/bin/bash
#SBATCH --job-name={job_name}    # Job name
#SBATCH --partition={backend}
#SBATCH --ntasks=1                    # Run on a single CPU
#SBATCH --time=336:00:00               # Time limit hrs:min:sec
#SBATCH --output={job_output_file}   # Standard output and error log
cd {job_directory}""".	format(
	job_directory=job_directory, 
	job_output_file=job_output_file,
	backend=backend,
	job_name=job_name
	)

	for f in input_files:
		sbatch_file += "\n/opt/oxdna/oxDNA/build/bin/oxDNA {file_name}".format(file_name=f)

	file_name = "sbatch.sh"
	file_path = job_directory + file_name

	file = open(file_path, "w+")
	file.write(sbatch_file)


def createOxDNAInput(parameters, job_directory, file_name, needs_relax):
	unique_parameters = parameters.copy()

	input_file_data = ""

	#one step jobs are a set length and run on a CPU
	if file_name == "input_one_step":
		unique_parameters["steps"] = 10
		unique_parameters["backend"] = "CPU"

		#the production run would fail, so we're checking the MC
		if needs_relax:
			if unique_parameters["interaction_type"] == "DNA2":
				unique_parameters["interaction_type"] = "DNA_relax"
			elif unique_parameters["interaction_type"] == "RNA2":
				unique_parameters["interaction_type"] = "RNA_relax"
			unique_parameters["dt"] = 0.05
			unique_parameters["lastconf_file"] = "MC_relax.dat"
			unique_parameters["sim_type"] = "MC"
			unique_parameters.update([("relax_type", "harmonic_force"), ("max_backbone_force", 10), ("delta_translation", 0.02), ("delta_rotation", 0.04)])


	#the initial relax is a set length, in monte-carlo on a CPU.
	if file_name == "input_relax_MC":
		if unique_parameters["interaction_type"] == "DNA2":
			unique_parameters["interaction_type"] = "DNA_relax"
		elif unique_parameters["interaction_type"] == "RNA2":
			unique_parameters["interaction_type"] = "RNA_relax"
		unique_parameters["sim_type"] = "MC"
		unique_parameters["steps"] = 100000
		unique_parameters["print_conf_interval"] = 50000
		unique_parameters["backend"] = "CPU"
		unique_parameters["dt"] = 0.05
		unique_parameters["lastconf_file"] = "MC_relax.dat"
		unique_parameters.update([("relax_type", "harmonic_force"), ("max_backbone_force", 10), ("delta_translation", 0.02), ("delta_rotation", 0.04)])

	#the secondary relax is a set length and run in molecular dynamics using GPU if requested
	if file_name == "input_relax_MD":
		unique_parameters["steps"] = 10000000
		unique_parameters["print_energy_interval"] = 5000000
		unique_parameters["dt"] = 0.0001
		unique_parameters["thermostat"] = "bussi"
		unique_parameters["T"] = "0C"
		unique_parameters["conf_file"] = "MC_relax.dat"
		unique_parameters["lastconf_file"] = "MD_relax.dat"
		unique_parameters["restart_step_counter"] = 0
		unique_parameters.update([("max_backbone_force", 1000), ("bussi_tau", 1)])
		if unique_parameters["backend"] == "CUDA":
			unique_parameters["backend_precision"] = "mixed"

	#the production run
	if file_name == "input":
		if needs_relax:
			unique_parameters["conf_file"] = "MD_relax.dat"
		if unique_parameters["backend"] == "CUDA":
			unique_parameters["backend_precision"] = "mixed"
 

	for (key, value) in unique_parameters.items():
		input_file_data += str(key) + " = " + str(value) + "\n"

	file_path = job_directory + file_name

	file = open(file_path, "w+")
	file.write(input_file_data)
	file.close()
	return(file_name)


def createOxDNAFile(parameters, job_directory, needs_relax=False):

	input_files = []
	
	createOxDNAInput(parameters, job_directory, "input_one_step", needs_relax)

	#if the needs relax checkbox is checked, you have to run a relax
	if needs_relax:
		input_files.append(createOxDNAInput(parameters, job_directory, "input_relax_MC", needs_relax))
		input_files.append(createOxDNAInput(parameters, job_directory, "input_relax_MD", needs_relax))

	#no matter what we're testing the input and running a job	
	input_files.append(createOxDNAInput(parameters, job_directory, "input", needs_relax))

	return(input_files)
	


def createAnalysisForUserIdWithJob(userId, jobId):
	cursor = cnx.cursor(buffered=True)

	randomAnalysisId = str(uuid.uuid4())

	user_directory = "/users/"+str(userId) + "/"
	job_directory = user_directory + jobId + "/"

	print("Now creating analysis file...")
	createSlurmAnalysisFile(job_directory, randomAnalysisId)
	job_number = startSlurmAnalysis(job_directory)

	print("Creating analysis now..., received job number:", job_number)

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

	user_directory = "/users/"+str(userId) + "/"
	job_directory = user_directory + randomJobId + "/"

	if not os.path.exists(user_directory):
		os.mkdir(user_directory)

	os.mkdir(job_directory)

	#pass randomJobId to slurm!
	files = jsonData["files"]

	#write the top and conf files
	for (file_name, file_data) in files.items():
		#set file path to /users here
		file_path = job_directory + file_name
		#print(file_directory)
		file = open(file_path, "w+")
		file.write(file_data)
		file.close()

	parameters = jsonData["parameters"]

	#needs_relax comes in as part of the simulation parameters, but it doesn't belong there.
	try:
		needs_relax = parameters["needs_relax"]
		parameters.pop("needs_relax")
	except:
		needs_relax = False
		pass
	
	#use the most up-to-date models
	if parameters["interaction_type"] == "DNA":
		parameters["interaction_type"] = "DNA2"

	elif parameters["interaction_type"] == "RNA":
		parameters["interaction_type"] = "RNA2"

	backend = parameters["backend"]
	if backend == "CUDA":
		backend = "GPU"
		parameters.update([	("CUDA_list", "verlet"), 
							("CUDA_sort_every", 0), 
							("use_edge", 1), 
							("edge_n_forces", 1)
		])
		


	input_files = createOxDNAFile(parameters, job_directory, needs_relax)
	createSlurmJobFile(job_directory, randomJobId, backend, input_files)
		
	
	#delay until we've ran one step job!
	job_ran_okay, error = runOneStepJob(job_directory)

	if not job_ran_okay:
		return False, error
	

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

	return True, job_number



def createJobDictionaryForTuple(data):

	job_id, user_id, job_name, uuid, slurm_id, job_type, analysis_job_id, creation_date, status= data

	schema = {
		"name":job_name,
		"uuid":uuid,
		"job_type":job_type,
		"analysisJobId":analysis_job_id,
		"creationDate":creation_date,
		"status":status,
	}

	return schema


def getJobsForUserId(userId):
	connection = Database.pool.get_connection()
	payload = []

	with connection.cursor() as cursor:
		cursor.execute(get_jobs_query, (int(userId),))
		result = cursor.fetchall()

		for data in result:
			job_data = createJobDictionaryForTuple(data)
			job_data["status"] = getJobStatus(data[3])
			payload.append(job_data)

	connection.close()

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


def runOneStepJob(job_directory):
	pipe = subprocess.Popen(
		["/opt/oxdna-cpu-only/oxDNA/build/bin/oxDNA", "input_one_step"], 
		stdout=subprocess.PIPE, 
		stderr=subprocess.PIPE,
		cwd=job_directory
	)
	stdout, stderr = pipe.communicate()

	'''
	print("OUT:", stdout)
	print("\n\n\n\n-------------_")
	print("ERR:", stderr)
	print("\n\n\n\n-------------_")
	print(len(stdout), len(stderr))
	print("\n\n\n\n-------------_")
	'''

	if len(stdout) == 0 and len(stderr) > 0:
		return False, stderr
	else:
		return True, None

def cancelJob(job_name):
	subprocess.Popen(["scancel", "-n", job_name], stdout=subprocess.PIPE)

	temp_cnx = mysql.connector.connect(user='root', password='', database='azdna')
	cursor = temp_cnx.cursor(buffered=True)

	
	cursor.execute(get_status, (job_name,))
	result = cursor.fetchone()
	prev_status = result[0]

	if prev_status == "Pending":
		cursor.execute(update_status, (job_name, "Canceled",))

	cursor.close()
	temp_cnx.close()

def deleteJob(job_uuid):
	print("Deleting Job")
	#need job name and user id
	#get user id
	temp_cnx = mysql.connector.connect(user='root', password='', database='azdna')

	cursor = temp_cnx.cursor(buffered=True)
	cursor.execute(get_userId_for_job_uuid, (job_uuid,))
	result = cursor.fetchone()
	userId = result[0]

	cursor.execute(remove_job, (job_uuid,))

	temp_cnx.commit()
	cursor.close()
	temp_cnx.close()
	

	job_path = "/users/" + str(userId) + "/" + job_uuid
	subprocess.Popen(["rm", "-R", job_path], stdout=subprocess.PIPE)




def getJobStatus(job_name):
	temp_cnx = mysql.connector.connect(user='root', password='', database='azdna')
	cursor = temp_cnx.cursor(buffered=True)
	
	pipe = subprocess.Popen(["squeue", "-n", job_name], stdout=subprocess.PIPE)
	output = pipe.communicate()[0].decode("ascii")[:-1]
	if output == "":
		return "None"
	
	try:
		code = output.split()[12]
	except:
		code = "NONE"

	status = code
	if code == "R":
		status = "Running"
	elif code == "PD":
		status = "Pending"
	elif code == "S":
		status = "Suspended"
	elif code == "CG":
		status = "Completing"
	elif code == "CD":
		status = "Completed"
	elif code == "NONE":
		cursor.execute(get_status, (job_name,))
		result = cursor.fetchone()
		status = result[0]
		if status == None:
			status = "Completed"
		
	
	cursor.execute(update_status, (job_name, status,))	

	temp_cnx.commit()
	cursor.close()
	temp_cnx.close()
	
	return status

	
	


	


#runOneStepJob("jobfiles/1/67423c24-6ee2-420e-af00-14f1e62c3362/")
#runOneStepJob("jobfiles/1/f776a944-54d4-4ff0-a6c1-65906be3872c")

	
