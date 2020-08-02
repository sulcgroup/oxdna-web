import os
import time
import uuid
import subprocess
import sys

import Delete_User_Files
import Database
import Cache

add_job_query = (
	"INSERT INTO Jobs "
	"(`userId`, `name`, `uuid`, `slurmId`, `jobType`, `simJobId`, `creationDate`)"
	"VALUES (%s, %s, %s, %s, %s, %s, %s)"
)

get_job_name_for_uuid = ("SELECT name FROM Jobs WHERE uuid = %s")
get_jobs_query = ("SELECT * FROM Jobs WHERE userId = %s")
get_job_query = ("SELECT * FROM Jobs WHERE uuid = %s")
get_associated_query = ("SELECT * FROM Jobs WHERE simJobId = %s")
get_userId_for_job_uuid = ("SELECT userID FROM Jobs WHERE uuid = %s")
remove_job = ("DELETE FROM Jobs WHERE uuid = %s")
remove_jobs_for_user_id = ("DELETE FROM Jobs WHERE userId = %s")
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



def createSlurmAnalysisFile(job_directory, analysis_id, analysis_type, analysis_parameters):
	job_output_file = job_directory + analysis_type + ".log"
	print("creating {type} analysis, id: {id}".format(type=analysis_type, id=analysis_id))

	if analysis_type == "mean":
		run_command = "compute_mean.py -p 1 -d deviations.json -f oxDNA -o mean.dat trajectory.dat output.top"
	elif analysis_type == "align":
		run_command = "align_trajectory.py trajectory.dat output.top aligned.dat"
	elif analysis_type == "distance":
		job_output_file = job_directory + analysis_parameters["name"] +".log"
		p1s = analysis_parameters["p1"].split(" ")
		p2s = analysis_parameters["p2"].split(" ")
		plist = []
		for pair in zip(p1s, p2s):
			plist.extend(pair)
		run_command = "distance.py -d {name}.txt -f both -o {name}.png -i input trajectory.dat {particles}".format(
			name = analysis_parameters["name"],
			particles = ' '.join(plist)
		)
	elif analysis_type == "bond":
		if ("force.txt" in os.listdir(job_directory)):
			run_command = "forces2pairs.py force.txt designed_pairs.txt"
		else:
			run_command = "generate_force.py -o force.txt -f designed_pairs.txt input last_conf.dat"
		run_command += ";python3 /opt/oxdna_analysis_tools/bond_analysis.py -p 1 input trajectory.dat designed_pairs.txt bond_occupancy.json"
	elif analysis_type == "angle_find":
		run_command = "duplex_angle_finder.py -p 1 -o duplex_angle.txt input trajectory.dat"
	elif analysis_type == "angle_plot":
		analysis_parameters["name"] = analysis_parameters["name_angle"]
		job_output_file = job_directory + analysis_parameters["name"] +".log"
		print("ANALYSIS PARAMATERS IANSIUEFALISEUFALIEUFALIWEUFHALISUEFHALISUEHFILFHAILUF")
		print("ANALYSIS PARAMATERS IANSIUEFALISEUFALIEUFALIWEUFHALISUEFHALISUEHFILFHAILUF")
		print("ANALYSIS PARAMATERS IANSIUEFALISEUFALIEUFALIWEUFHALISUEFHALISUEHFILFHAILUF")
		print(analysis_parameters)
		print(analysis_id)
		print(analysis_type)
		p1 = analysis_parameters["p1"]
		p2 = analysis_parameters["p2"]
		plist = [p1, p2]
		run_command = "duplex_angle_plotter.py -f both -o {name}.png -i duplex_angle.txt {particles}".format(
			name = analysis_parameters["name"],
			particles = ' '.join(plist)
		)

	sbatch_file = """#!/bin/bash
#SBATCH --job-name={analysis_id}    # Job name
#SBATCH --partition=CPU
#SBATCH --ntasks=1                    # Run on a single CPU
#SBATCH --time=100:00:00               # Time limit hrs:min:sec
#SBATCH -o {job_output_file}
#SBATCH -e {job_output_file}
cd {job_directory}
python3 /opt/oxdna_analysis_tools/{run_command}""".format(
	analysis_id=analysis_id,
	job_directory=job_directory, 
	job_output_file=job_output_file,
	run_command=run_command
)

	file_name = "sbatch_analysis.sh"
	file_path = job_directory + file_name


	print("Creating analysis file at filepath:", file_path)

	file = open(file_path, "w+")
	file.write(sbatch_file)

def createSlurmJobFile(job_directory, job_name, backend, input_files, force=1.5):
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
		if f == "input_relax_MC":
			sbatch_file += "\n/opt/oxdna_analysis_tools/generate_force.py -o force.txt input_relax_MC MC_relax.dat"
			sbatch_file += '\nsed -i "s/0.9/{force}/g" force.txt'.format(force=force)
	sbatch_file += "\npython3 /opt/zip_traj.py"

	file_name = "sbatch.sh"
	file_path = job_directory + file_name

	file = open(file_path, "w+")
	file.write(sbatch_file)


def createOxDNAInput(parameters, job_directory, file_name, needs_relax):
	unique_parameters = parameters.copy()
	unique_parameters.pop("MC_steps")
	unique_parameters.pop("MD_steps")
	unique_parameters.pop("MD_dt")

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
			unique_parameters.update([("relax_type", "harmonic_force"), ("max_backbone_force", 10), ("delta_translation", 0.22), ("delta_rotation", 0.22)])


	#the initial relax is a set length, in monte-carlo on a CPU.
	if file_name == "input_relax_MC":
		if unique_parameters["interaction_type"] == "DNA2":
			unique_parameters["interaction_type"] = "DNA_relax"
		elif unique_parameters["interaction_type"] == "RNA2":
			unique_parameters["interaction_type"] = "RNA_relax"
		unique_parameters["sim_type"] = "MC"
		unique_parameters["steps"] = parameters["MC_steps"]
		unique_parameters["print_conf_interval"] = 50000
		unique_parameters["backend"] = "CPU"
		unique_parameters["dt"] = 0.05
		unique_parameters["lastconf_file"] = "MC_relax.dat"
		unique_parameters.update([("relax_type", "harmonic_force"), ("max_backbone_force", 10), ("delta_translation", 0.22), ("delta_rotation", 0.22)])

	#the secondary relax is a set length and run in molecular dynamics using GPU if requested
	if file_name == "input_relax_MD":
		unique_parameters["steps"] = parameters["MD_steps"]
		unique_parameters["print_energy_interval"] = 5000000
		unique_parameters["dt"] = parameters["MD_dt"]
		unique_parameters["thermostat"] = "bussi"
		unique_parameters["T"] = "0C"
		unique_parameters["conf_file"] = "MC_relax.dat"
		unique_parameters["lastconf_file"] = "MD_relax.dat"
		unique_parameters["restart_step_counter"] = 0
		unique_parameters.update([("max_backbone_force", 1000), ("bussi_tau", 1), ("external_force", 1), ("external_force_file", "force.txt")])
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
	


def createAnalysisForUserIdWithJob(userId, analysis_parameters):
	analysis_types = {
		"mean" : 1,
		"align" : 2,
		"distance" : 3,
		"bond" : 4,
		"angle_find" : 5,
		"angle_plot" : 6
	}

	jobId = analysis_parameters["jobId"]
	analysis_type = analysis_parameters["type"]
	print(analysis_type)
	print(analysis_parameters)
	if analysis_type == "mean":
		analysis_parameters["name"] = "mean"
	elif analysis_type == "align":
		analysis_parameters["name"] = "align"
	elif analysis_type == "bond":
		analysis_parameters["name"] = "bond"
	elif analysis_type == "angle_find":
		analysis_parameters["name"] = "angle_find"

	randomAnalysisId = str(uuid.uuid4())

	user_directory = "/users/"+str(userId) + "/"
	job_directory = user_directory + jobId + "/"

	print("Now creating analysis file...")
	createSlurmAnalysisFile(job_directory, randomAnalysisId, analysis_type, analysis_parameters)
	job_number = startSlurmAnalysis(job_directory)

	print("Creating analysis now..., received job number:", job_number)

	update_data = (
		jobId,
		randomAnalysisId
	)

	connection = Database.pool.get_connection()

	analysis_data = (
		int(userId),
		analysis_parameters["name"],
		randomAnalysisId,
		job_number,
		analysis_types[analysis_type],
		jobId,
		int(time.time())
	)

	with connection.cursor() as cursor:
		cursor.execute(add_job_query, analysis_data)
	
	connection.close()

	return randomAnalysisId


def createJobForUserIdWithData(userId, jsonData):
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
		relax_force = parameters["relax_force"]
		parameters.pop("relax_force")
	except:
		relax_force = 0
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
	createSlurmJobFile(job_directory, randomJobId, backend, input_files, force=relax_force)
		
	
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

	connection = Database.pool.get_connection()

	with connection.cursor() as cursor:
		cursor.execute(add_job_query, job_data)
	
	connection.close()

	return True, job_number

def getAssociatedJobs(job_id):
	associates = None
	payload = []

	#retrieve entries from SQL with sim_job_id == jobId
	connection = Database.pool.get_connection()
	with connection.cursor() as cursor:
		cursor.execute(get_associated_query, (job_id,))
		associates = cursor.fetchall()
	connection.close()

	if associates:
		for job_data in associates:
			data_dict = createAssociateDictionary(job_data)
			data_dict["status"] = getJobStatus(data_dict["uuid"])
			payload.append(data_dict)
		return payload
	else:
		return None


def createAssociateDictionary(data) :
	keys = ["name", "uuid", "job_type", "sim_job_id", "creation_date", "status"]
	data = [data[i] for i in [2, 3, 5, 6, 7, 8]]
	schema = dict(zip(keys, data))

	return schema

def createJobDictionaryForTuple(data):

	job_id, user_id, job_name, uuid, slurm_id, job_type, sim_job_id, creation_date, status= data

	schema = {
		"name":job_name,
		"uuid":uuid,
		"job_type":job_type,
		"creation_date":creation_date,
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
	connection = Database.pool.get_connection()

	result = None

	with connection.cursor() as cursor:
		cursor.execute(get_job_query, (jobId,))
		result = cursor.fetchone()

	connection.close()

	if result is not None:
		return createJobDictionaryForTuple(result)
	else:
		return None

def getJobNameForUuid(uuid):
	connection = Database.pool.get_connection()

	result = None

	with connection.cursor() as cursor:
		cursor.execute(get_job_name_for_uuid, (uuid,))
		result = cursor.fetchone()
	
	connection.close()
	
	if result is not None:
		return result[0]
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

	connection = Database.pool.get_connection()

	prev_status = None

	with connection.cursor() as cursor:
		cursor.execute(get_status, (job_name,))
		result = cursor.fetchone()
		prev_status = result[0]

	if prev_status == "Pending":
		cursor.execute(update_status, ("Canceled", job_name,))

	connection.close()

def deleteJob(job_uuid):
	print("Deleting Job")
	#need job name and user id
	#get user id

	user_id = None

	connection = Database.pool.get_connection()

	with connection.cursor() as cursor:
		cursor.execute(get_userId_for_job_uuid, (job_uuid,))
		result = cursor.fetchone()
		user_id = result[0]

	with connection.cursor() as cursor:
		cursor.execute(remove_job, (job_uuid,))

	
	connection.close()
	

	job_path = "/users/" + str(user_id) + "/" + job_uuid
	subprocess.Popen(["rm", "-R", job_path], stdout=subprocess.PIPE)

def deleteJobsForUser(user_id):
	Delete_User_Files.deleteUser(user_id)

	connection = Database.pool.get_connection()
	with connection.cursor() as cursor:
		cursor.execute(remove_jobs_for_user_id, (user_id,))
	
	connection.close()

def getJobStatusFromSlurm(job_name):
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
		status = None

	return status
	

def getJobStatus(job_name):	
	#Check the cache for completed jobs
	#we can save on doing the Slurm/MySQL interfacing
	cache_entry = Cache.CompletedJobsCache.get(job_name)
	if cache_entry: 
		print("Found CompletedJobsCache entry for:", job_name)
		return cache_entry
	else:
		print("Did not find entry for:", job_name)

	connection = Database.pool.get_connection()
	
	status = getJobStatusFromSlurm(job_name)

	#if it was still not found,
	#we can assume the job has completed
	#and we won't see further updates
	if status == None:
		status = "Completed"
		Cache.CompletedJobsCache.set(job_name, status)

	#update the job status
	#maybe we can eventually have a cronjob running to actually handle these updates
	#that would make this interface a lot more REST-y too
	#would just query MySQL only, without ever having to look at the squeue
	with connection.cursor() as cursor:
		print("JOB NAME: ", job_name)
		cursor.execute(update_status, (status, job_name,))	

	connection.close()
	return status
