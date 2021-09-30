import os
import time
import uuid
import subprocess
import sys
from math import ceil

import Delete_User_Files
import Database
import Cache
import Admin
import Utilities
from EmailScript import SendEmail


add_job_query = (
	"INSERT INTO Jobs "
	"(`userId`, `name`, `uuid`, `slurmId`, `jobType`, `simJobId`, `creationDate`)"
	"VALUES (%s, %s, %s, %s, %s, %s, %s)"
)

get_job_name_for_uuid = ("SELECT name FROM Jobs WHERE uuid = %s")
get_jobs_query = ("SELECT * FROM Jobs WHERE userId = %s")
get_job_query = ("SELECT * FROM Jobs WHERE uuid = %s")
get_associated_query = ("SELECT * FROM Jobs WHERE simJobId = %s")
update_job_name = ("UPDATE Jobs SET name = %s WHERE uuid = %s")
get_userId_for_job_uuid = ("SELECT userId FROM Jobs WHERE uuid = %s")
remove_job = ("DELETE FROM Jobs WHERE uuid = %s")
remove_jobs_for_user_id = ("DELETE FROM Jobs WHERE userId = %s")
get_status = ("SELECT status FROM Jobs WHERE uuid = %s")
update_status = ("UPDATE Jobs SET status = %s WHERE uuid = %s")
get_firstname_for_uuid = ("SELECT u.firstName from Jobs j JOIN Users u on j.userId=u.id WHERE j.uuid=%s")

def getUserIdForJob(job_id):
	result = None
	with Database.pool.get_connection() as connection:
		with connection.cursor() as cursor:
			cursor.execute(get_userId_for_job_uuid, (job_id,))
			try:
				result = cursor.fetchone()[0]
			except: #throws in index error if there is no such job.
				return None

	return result

def startSlurmJob(job_directory):
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
	print("creating {type} analysis, id: {id}".format(type=analysis_type, id=analysis_id), flush=True)

	#if this is running in the virtual machine, which only has 1 cpu, var will not be in the path
	#But on the server, which has 20, its okay to give 5 cpus to a job.
	home_path = Utilities.get_home_path()
	if 'var' in home_path:
		allocation = 5
	else:
		allocation = 1

	cpu_allocation = {
		"mean" : allocation,
		"align" : 1,
		"distance" : 1,
		"bond" : allocation,
		"angle_find" : allocation,
		"angle_plot" : 1,
		"energy" : 1
	}

	if analysis_type == "mean":
		run_command = "compute_mean.py -p {n} -d deviations.json -f oxDNA -o mean.dat trajectory.dat".format(n = cpu_allocation[analysis_type])
	elif analysis_type == "align":
		run_command = "align_trajectory.py trajectory.dat aligned.dat\npython3 /opt/zip_traj.py aligned.dat aligned.zip\nrm aligned.dat"
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
			run_command = "generate_force.py -o force.txt -f designed_pairs.txt input output.dat"
		run_command += ";python3 /opt/oxdna_analysis_tools/bond_analysis.py -p {n} input trajectory.dat designed_pairs.txt bond_occupancy.json".format(n = cpu_allocation[analysis_type])
	elif analysis_type == "angle_find":
		run_command = "duplex_angle_finder.py -p {n} -o duplex_angle.txt input trajectory.dat".format(n = cpu_allocation[analysis_type])
	elif analysis_type == "angle_plot":
		analysis_parameters["name"] = analysis_parameters["name_angle"]
		job_output_file = job_directory + analysis_parameters["name"] + ".log"
		p1 = analysis_parameters["p1_angle"].split(" ")
		p2 = analysis_parameters["p2_angle"].split(" ")
		p_input = []
		for pair in zip(p1, p2):
			p_input.append("-i duplex_angle.txt " + " ".join(pair))
		run_command = "duplex_angle_plotter.py -f both -o {name}.png {particle_input}".format(
			name = analysis_parameters["name"],
			particle_input = ' '.join(p_input)
		)
	elif analysis_type == "energy":
		job_output_file = job_directory + analysis_parameters["name"] + ".log"
		run_command = "plot_energy.py -f both -o {}.png energy.dat".format(analysis_parameters["name"])

	sbatch_file = """#!/bin/bash
#SBATCH --job-name={analysis_id}    # Job name
#SBATCH --partition=CPU
#SBATCH --ntasks={n}                    # Run on a single CPU
#SBATCH --time=48:00:00               # Time limit hrs:min:sec
#SBATCH -o {job_output_file}
#SBATCH -e {job_output_file}
cd {job_directory}
python3 /opt/oxdna_analysis_tools/{run_command}""".format(
	analysis_id=analysis_id,
	job_directory=job_directory, 
	job_output_file=job_output_file,
	run_command=run_command,
	n=cpu_allocation[analysis_type]
)

	file_name = "sbatch_analysis.sh"
	file_path = job_directory + file_name


	print("Creating analysis file at filepath:", file_path)

	file = open(file_path, "w+")
	file.write(sbatch_file)

def createSlurmJobFile(job_directory, job_name, backend, interaction, input_files, force=1.5):
	home_path = Utilities.get_home_path()

	#job_output_location = job_directory
	job_output_file = job_directory + "job_out.log"
	if backend == "CPU":
		sbatch_file = """#!/bin/bash
#SBATCH --job-name={job_name}    # Job name
#SBATCH --partition={backend}
#SBATCH --ntasks=1                    # Run on a single CPU
#SBATCH --time=96:00:00               # Time limit hrs:min:sec
#SBATCH --output={job_output_file}   # Standard output and error log
cd {job_directory}""".	format(
	job_directory=job_directory, 
	job_output_file=job_output_file,
	backend=backend,
	job_name=job_name
	)
		if interaction == "DNANM" or interaction == "RNANM":
			oxdna_binary = "/opt/anm-oxdna_cpu/oxDNA/build/bin/oxDNA"
		else:
			oxdna_binary = "/opt/oxdna-cpu-only/oxDNA/build/bin/oxDNA"
	
	else:
		sbatch_file = """#!/bin/bash
#SBATCH --job-name={job_name}    # Job name
#SBATCH --partition={backend}
#SBATCH --ntasks=1                    # Run on a single CPU
#SBATCH --time=96:00:00               # Time limit hrs:min:sec
#SBATCH --output={job_output_file}   # Standard output and error log
cd {job_directory}""".	format(
	job_directory=job_directory, 
	job_output_file=job_output_file,
	backend=backend,
	job_name=job_name
	)
		if interaction == "DNANM" or interaction == "RNANM":
			oxdna_binary = "/opt/anm-oxdna/oxDNA/build/bin/oxDNA"
		else:
			oxdna_binary = "/opt/oxdna/oxDNA/build/bin/oxDNA"

	for f in input_files:
		sbatch_file += "\n{oxdna_binary} {file_name}".format(oxdna_binary = oxdna_binary, file_name=f)
		if f == "input_relax_MC":
			sbatch_file += "\n/opt/oxdna_analysis_tools/generate_force.py -o force.txt input_relax_MC MC_relax.dat"
			sbatch_file += "\nsed -i 's/0\.9/{force}/g' force.txt".format(force=force)
	sbatch_file += "\npython3 /opt/zip_traj.py trajectory.dat trajectory.zip"
	sbatch_file += "\npython3 {path}/Update_Status.py".format(path=home_path)

	file_name = "sbatch.sh"
	file_path = job_directory + file_name

	file = open(file_path, "w+")
	file.write(sbatch_file)


def createOxDNAInput(parameters, job_directory, file_name, needs_relax):
	#Copying parameters let us change parameters if we're making multiple input files from the same form submission
	#There are three input files created if relaxion was requested
	unique_parameters = parameters.copy()

	#these parameters are not actually oxDNA commands, so we remove them from the dict that actually creates the input file
	unique_parameters.pop("MC_steps")
	unique_parameters.pop("MD_steps")
	unique_parameters.pop("MD_dt")

	input_file_data = ""

	#one step jobs are a set length and run on a CPU
	if file_name == "input_one_step":
		unique_parameters["steps"] = 10
		unique_parameters["backend"] = "CPU"

		#the production run would fail, so we're checking the MC if relaxing
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
		unique_parameters["steps"] = parameters["MC_steps"]
		unique_parameters["print_energy_every"] = ceil(parameters["MC_steps"] / 10)
		unique_parameters["print_conf_interval"] = ceil(parameters["MC_steps"] / 10)
		unique_parameters["backend"] = "CPU"
		unique_parameters["dt"] = 0.05
		unique_parameters["lastconf_file"] = "MC_relax.dat"
		unique_parameters.update([("relax_type", "harmonic_force"), ("max_backbone_force", 10), ("delta_translation", 0.22), ("delta_rotation", 0.22)])

	#the secondary relax is a set length and run in molecular dynamics using GPU if requested
	if file_name == "input_relax_MD":
		unique_parameters["steps"] = parameters["MD_steps"]
		unique_parameters["print_energy_every"] = ceil(parameters["MD_steps"] / 10)
		unique_parameters["print_conf_interval"] = ceil(parameters["MD_steps"] / 10)
		unique_parameters["dt"] = parameters["MD_dt"]
		unique_parameters["thermostat"] = "bussi"
		unique_parameters["T"] = "0C"
		unique_parameters["conf_file"] = "MC_relax.dat"
		unique_parameters["lastconf_file"] = "MD_relax.dat"
		unique_parameters["restart_step_counter"] = 0
		unique_parameters.update([("max_backbone_force", 1000), ("bussi_tau", 1), ("external_forces", 1), ("external_forces_file", "force.txt")])
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
		"angle_plot" : 6,
		"energy" : 7
	}

	jobId = analysis_parameters["jobId"]
	analysis_type = analysis_parameters["type"]
	if analysis_type == "mean":
		analysis_parameters["name"] = "mean"
	elif analysis_type == "align":
		analysis_parameters["name"] = "align"
	elif analysis_type == "bond":
		analysis_parameters["name"] = "bond"
	elif analysis_type == "angle_find":
		analysis_parameters["name"] = "angle_find"
	elif analysis_type == "energy":
		analysis_parameters["name"] = "energy"

	randomAnalysisId = str(uuid.uuid4())

	user_directory = "/users/"+str(userId) + "/"
	job_directory = user_directory + jobId + "/"

	createSlurmAnalysisFile(job_directory, randomAnalysisId, analysis_type, analysis_parameters)
	job_number = startSlurmAnalysis(job_directory)

	print("Creating analysis for user {}, received job number: {}".format(userId, job_number), flush=True)

	update_data = (
		jobId,
		randomAnalysisId
	)

	with Database.pool.get_connection() as connection:

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

	return randomAnalysisId


def createJobForUserIdWithData(userId, jsonData, randomJobId):
	user_directory = "/users/"+str(userId) + "/"
	job_directory = user_directory + randomJobId + "/"
	print("Creating job {uuid} for user {user}".format(uuid=randomJobId, user=userId), flush=True)

	if not os.path.exists(user_directory):
		os.mkdir(user_directory)

	os.mkdir(job_directory)

	#pass randomJobId to slurm!
	files = jsonData["files"]

	#write the top, conf, and (optional) par and force files
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
	interaction = parameters["interaction_type"]
	if interaction == "DNA":
		parameters["interaction_type"] = "DNA2"

	elif interaction == "RNA":
		parameters["interaction_type"] = "RNA2"
	interaction = parameters["interaction_type"]

	#Protein simulations can be very dense.
	if interaction == "DNANM" or interaction == "RNANM":
		parameters["max_density_multiplier"] = 200

	backend = parameters["backend"]
	if backend == "CUDA":
		backend = "GPU"
		parameters.update([	("CUDA_list", "verlet"), 
							("CUDA_sort_every", 0), 
							("use_edge", 1), 
							("edge_n_forces", 1)
		])

	#empty optional parameters need to be removed from the list
	to_remove = []
	for key in parameters.keys():
		if parameters[key] == '':
			to_remove.append(key)

	for key in to_remove:
		parameters.pop(key)
			
	#if parameters["external_forces_file"] == '':
	#	parameters.pop("external_forces_file")

	print(parameters["use_average_seq"], flush=True)
	if parameters["use_average_seq"] == 0:
		print(interaction, flush=True)
		if interaction == "DNA2" or interaction == "DNANM":
			parameters.update({"seq_dep_file":"/opt/oxdna/oxDNA/oxDNA2_sequence_dependent_parameters.txt"})
		if interaction == "RNA2" or interaction == "RNANM":
			parameters.update({"seq_dep_file":"/opt/oxdna/oxDNA/rna_sequence_dependent_parameters.txt"})

	input_files = createOxDNAFile(parameters, job_directory, needs_relax)
	createSlurmJobFile(job_directory, randomJobId, backend, interaction, input_files, force=relax_force)
		
	
	#delay until we've ran one step job!
	job_ran_okay, error = runOneStepJob(job_directory, interaction)

	if not job_ran_okay:
		print("Job {uuid} died on one-step run".format(uuid=randomJobId), flush=True)
		return False, error
	

	job_number = startSlurmJob(job_directory)
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

	with Database.pool.get_connection() as connection:
		with connection.cursor() as cursor:
			cursor.execute(add_job_query, job_data)
	
	print("Successfully created job {uuid} for user {user}".format(uuid=randomJobId, user=userId), flush=True)

	return True, job_number

def getAssociatedJobs(job_id):
	associates = None
	payload = []

	#retrieve entries from SQL with sim_job_id == jobId
	with Database.pool.get_connection() as connection:
		with connection.cursor() as cursor:
			cursor.execute(get_associated_query, (job_id,))
			associates = cursor.fetchall()

	if associates:
		for job_data in associates:
			data_dict = createAssociateDictionary(job_data)
			data_dict["status"] = getJobStatus(data_dict["uuid"])
			payload.append(data_dict)
		return payload
	else:
		return None

def isRelax(job_id):
	with Database.pool.get_connection() as connection:
		with connection.cursor() as cursor:
			cursor.execute(get_userId_for_job_uuid, (job_id,))
			user_id = cursor.fetchone()[0]
	
	job_files = os.listdir("/users/{}/{}".format(user_id, job_id))
	return "True" if "MD_relax.dat" in job_files else "False"

def availableFiles(job_id):
	with Database.pool.get_connection() as connection:
		with connection.cursor() as cursor:
			cursor.execute(get_userId_for_job_uuid, (job_id,))
			user_id = cursor.fetchone()[0]

	job_files = set(os.listdir("/users/{}/{}".format(user_id, job_id)))
	files = {
		"input" : "True" if "input" in job_files else "False",
		"energy" : "True" if "energy.dat" in job_files else "False",
		"log" : "True" if "job_out.log" in job_files else "False",
		"top" : "True" if "output.top" in job_files else "False",
		"first" : "True" if "output.dat" in job_files else "False",
		"last" : "True" if "last_conf.dat" in job_files else "False",
		"traj" : "True" if "trajectory.zip" in job_files else "False"
	}
	return files

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
	payload = []
	with Database.pool.get_connection() as connection:
		with connection.cursor() as cursor:
			cursor.execute(get_jobs_query, (int(userId),))
			result = cursor.fetchall()

			for data in result:
				job_data = createJobDictionaryForTuple(data)
				job_data["status"] = getJobStatus(data[3])
				payload.append(job_data)

	return payload

def getJobFromUuid(jobId):
	result = None

	with Database.pool.get_connection() as connection:
		with connection.cursor() as cursor:
			cursor.execute(get_job_query, (jobId,))
			result = cursor.fetchone()

	if result is not None:
		return createJobDictionaryForTuple(result)
	else:
		return None

def getJobNameForUuid(uuid):
	result = None

	with Database.pool.get_connection() as connection:
		with connection.cursor() as cursor:
			cursor.execute(get_job_name_for_uuid, (uuid,))
			result = cursor.fetchone()
	
	if result is not None:
		return result[0]
	else:
		return None

def getFirstNameForUuid(uuid):
	result = None
	with Database.pool.get_connection() as connection:
		with connection.cursor() as cursor:
			cursor.execute(get_firstname_for_uuid, (uuid,))
			result = cursor.fetchone()
	
	if result is not None:
		return result[0]
	else:
		return None

def updateJobName(name, uuid):
	with Database.pool.get_connection() as connection:
		with connection.cursor() as cursor:
			cursor.execute(update_job_name, (name, uuid,))
	
	return name

def runOneStepJob(job_directory, interaction):
	if interaction == "DNANM" or interaction == "RNANM":
		oxdna_binary = "/opt/anm-oxdna_cpu/oxDNA/build/bin/oxDNA"
	else:
		oxdna_binary = "/opt/oxdna-cpu-only/oxDNA/build/bin/oxDNA"
	pipe = subprocess.Popen(
		[oxdna_binary, "input_one_step"], 
		stdout=subprocess.PIPE, 
		stderr=subprocess.PIPE,
		cwd=job_directory
	)
	stdout, stderr = pipe.communicate()

	if len(stdout) == 0 and len(stderr) > 0:
		return False, stderr
	else:
		return True, None
	
def updateStatus(user_id, job_uuid):
	with Database.pool.get_connection() as connection:

		with connection.cursor() as cursor:
			cursor.execute("UPDATE Jobs SET status = \"Completed\" WHERE uuid = %s", (job_uuid))

		with connection.cursor() as cursor:
			cursor.execute("SELECT creationDate FROM Jobs WHERE uuid = %s", (job_uuid,))
			creation_time = int(cursor.fetchone()[0])

		elapsed_time = time.time() - creation_time
		new_time_limit = Admin.getTimeLimit(user_id) - elapsed_time
		if new_time_limit < 0:
			new_time_limit = 0

		with connection.cursor() as cursor:
			cursor.execute("UPDATE Users SET timeLimit = %s WHERE id = %s", (new_time_limit, user_id))

	print("Remaining monthly time limit: ", str(new_time_limit), " seconds")

def cancelJob(job_name):
	subprocess.Popen(["scancel", "-n", job_name], stdout=subprocess.PIPE)

	user_id = None
	with Database.pool.get_connection() as connection:
		with connection.cursor() as cursor:
			cursor.execute(get_userId_for_job_uuid, (job_name,))
			result = cursor.fetchone()
			user_id = result[0]
		updateStatus(user_id, job_name)

		prev_status = None

		with connection.cursor() as cursor:
			cursor.execute(get_status, (job_name,))
			result = cursor.fetchone()
			prev_status = result[0]

		if prev_status == "Pending":
			cursor.execute(update_status, ("Canceled", job_name,))

def deleteJob(job_uuid):
	print("Deleting Job {}".format(job_uuid), flush=True)
	#need job name and user id
	#get user id

	user_id = None

	with Database.pool.get_connection() as connection:
		with connection.cursor() as cursor:
			cursor.execute(get_userId_for_job_uuid, (job_uuid,))
			result = cursor.fetchone()
			user_id = result[0]

		with connection.cursor() as cursor:
			cursor.execute(remove_job, (job_uuid,))

	job_path = "/users/" + str(user_id) + "/" + job_uuid
	subprocess.Popen(["rm", "-R", job_path], stdout=subprocess.PIPE)

def deleteJobsForUser(user_id):
	Delete_User_Files.deleteUser(user_id)

	with Database.pool.get_connection() as connection:
		with connection.cursor() as cursor:
			cursor.execute(remove_jobs_for_user_id, (user_id,))

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
		#print("Found CompletedJobsCache entry for:", job_name)
		return cache_entry
	#else:
		#print("Did not find entry for:", job_name)

	with Database.pool.get_connection() as connection:
	
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
			#print("JOB NAME: ", job_name)
			cursor.execute(update_status, (status, job_name,))	

	return status

def getQueue():
	pipe = subprocess.Popen(["squeue"], stdout=subprocess.PIPE)
	output = pipe.communicate()[0].decode("ascii")
	jobs = output.split('\n')[1:]

	running = queued = 0
	for job in jobs:
		if ' R ' in job:
			running += 1
		elif ' PD ' in job:
			queued += 1
	
	return str(running) + ' ' + str(queued)
