import os
from flask import Flask, Response, request, send_file, session, jsonify, redirect, render_template
import requests

import Login
import Job
import Register

app = Flask(__name__, static_url_path='/static', static_folder="static")
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

def addDefaultParameters(parameters):
	default_parameters = {
		"verlet_skin":1,
		"time_scale":"linear",
		"ensemble":"NVT",
		"dt":"0.001",
		"backend_precision":"double",
		"trajectory_file":"trajectory.dat",
		"energy_file":"energy.dat",
		"refresh_vel":1,
		"restart_step_counter":1
	}

	for (key, value) in default_parameters.items():
		if key not in parameters:
			parameters[key] = default_parameters[key]

@app.route('/create_job', methods=['POST'])
def handle_form():

	if session.get("user_id") is None:
		return "You must be logged in to submit a job!"

	user_id = session["user_id"]
	print("Now creating a job on behalf of:", user_id)

	json_data = request.get_json()

	parameters = json_data["parameters"]
	files = json_data["files"]

	addDefaultParameters(parameters)

	metadata = {}

	job_data = {
		"metadata":metadata,
		"parameters": parameters, 
		"files": files
	}

	Job.createJobForUserIdWithData(user_id, job_data)

	return "Uploaded!"


@app.route("/register", methods=["GET", "POST"])
def register():

	if request.method == "GET":
		return send_file("templates/register.html")

	if request.method == "POST":
		username = request.form["username"]
		password = request.form["password"]

	if username is not None and password is not None:
		user_id = Register.registerUser(username, password)

		if(user_id != -1):
			session["user_id"] = user_id
			return redirect("/")
		else:
			return "Invalid username or password"

	return "Invalid username or password"


@app.route("/login", methods=["GET", "POST"])
def login():

	if request.method == "GET":
		return send_file("templates/login.html")

	if request.method == "POST":
		username = request.form["username"]
		password = request.form["password"]
	if username is not None and password is not None:
		user_id = Login.loginUser(username, password)

		if(user_id != -1):
			session["user_id"] = user_id
			return redirect("/")
		else:
			return "Invalid username or password"

	return "Invalid username or password"

@app.route("/logout")
def logout():
	session["user_id"] = None
	return "You have logged out"


@app.route("/account", methods=["GET"])
def account():

	if session.get("user_id") is None:
		return "You must be logged in to modify your account"

	if request.method == "GET":
		return send_file("templates/account.html")

@app.route("/account/update_password", methods=["POST"])
def updatePassword():
	if session.get("user_id") is None:
		return "You must be logged in to modify your account"

	user_id = int(session["user_id"])

	old_password = request.json["old_password"]
	new_password = request.json["new_password"]

	return Login.updatePasssword(user_id, old_password, new_password)

@app.route("/account/get_email", methods=["GET"])
def updateEmail():
	if session.get("user_id") is None:
		return "You must be logged in to modify your account"

	user_id = int(session["user_id"])
	
	return Account.getEmail(user_id)

@app.route("/account/set_email", methods=["POST"])
def updateEmail():
	if session.get("user_id") is None:
		return "You must be logged in to modify your account"

	user_id = int(session["user_id"])
	email_new = string(session["email"])
	
	return Account.setEmail(user_id, email_new)

@app.route("/account/get_status", methods=["GET"])
def updateEmail():
	if session.get("user_id") is None:
		return "You must be logged in to modify your account"

	user_id = int(session["user_id"])
	
	return Account.getStatus(user_id)

@app.route("/account/get_creation_date", methods=["GET"])
def updateEmail():
	if session.get("user_id") is None:
		return "You must be logged in to modify your account"

	user_id = int(session["user_id"])
	
	return Account.get_creation_date(user_id)

#render the jobs template page
@app.route("/jobs")
def jobs():

	if session.get("user_id") is None:
		return redirect("/login")
	else:
		return send_file("templates/jobs.html")

@app.route("/all_jobs")
def getJobs():

	if session.get("user_id") is None:
		return "You must be logged in to view your jobs"

	user_id = int(session["user_id"])

	jobs = Job.getJobsForUserId(user_id)

	return jsonify(jobs)


@app.route("/job_output/<uuid>/<desired_output>")
def getJobOutput(uuid, desired_output):

	if session.get("user_id") is None:
		return "You must be logged in to view the output of a job"

	desired_output_map = {
		"energy":"energy.dat",
		"trajectory":"trajectory.dat",
		"log":"job_out.log",
		"input":"input"
	}

	if desired_output not in desired_output_map:
		return "You must specify a valid desired output"
	

	user_directory = "jobfiles/" + str(session["user_id"]) + "/"
	job_directory =  user_directory + uuid + "/"
	desired_file_path = job_directory + desired_output_map[desired_output]

	desired_file = open(desired_file_path, "r")




	desired_file_contents = desired_file.read()

	return Response(desired_file_contents, mimetype='text/plain')


@app.route("/")
def index():

	if session.get("user_id") is not None:
		return render_template("index.html")
	else:
		return redirect("/login")

app.run(host="0.0.0.0", port=9000)