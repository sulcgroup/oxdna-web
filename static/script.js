var app = angular.module("app", [])

app.factory("JobService", function($http) {

	var factory = {};

	factory.getJob = function(jobId, cb) {
		$http({
			method: 'GET',
			url: `/api/job/${jobId}`
		}).then(function successCallback(response) {

			var data = response.data;
			console.log(data);

			cb(data);
		}, function errorCallback() {
			cb([]);
		});
	}

	factory.startAnalysisForJob = function(jobId, cb) {
		$http({
			method: 'POST',
			url: `/api/create_analysis/${jobId}`,
		}).then(function success(analysisId) {
			console.log("Created analysis!");
			cb(true, analysisId);

		}, function error() {
			console.log("Failed to create analysis!");
			cb(false);
		});
	}

	return factory;

})


app.factory("JobsService", function($http) {

	var factory = {};

	factory.getJobs = function(cb) {
		$http({
			method: 'GET',
			url: '/all_jobs'
		}).then(function successCallback(response) {

			var data = response.data;

			for(job in data) {
				var timestamp = data[job]["creationDate"];
				var date = new Date(timestamp * 1000).toLocaleString("en-US");			
				data[job]["dateString"] = date;
			}

			data.sort((a,b) => parseInt(b["creationDate"]) - parseInt(a["creationDate"]));
			data = data.filter(x => x.job_type == 0);

			cb(data);
		}, function errorCallback() {````
			cb([]);
		});
	}

	return factory;

})

app.controller("AppCtrl", function($scope, JobsService) {
	
	$scope.job_history = [];

	JobsService.getJobs(function(jobs) {
		$scope.job_history = jobs;
	})


})

app.controller("AccountCtrl", function($scope, $http) {

	$scope.status = null;

	console.log("Now in the acccount ctrl!");

	$scope.updatePassword = function(old_password, new_password) {
		$scope.status = "Loading...";

		$http({
			method: 'POST',
			data: 
			{
				"old_password":old_password,
				"new_password":new_password
			},
			url: '/account/update_password'
		}).then(function (response) {

			var data = response.data;

			if(data == "Invalid password") {
				$scope.status = "Invalid password";
			} else if(data == "Password updated") {
				$scope.status = "Password updated";
			}
		
		});
	}

	$scope.submit = function() {
		$scope.updatePassword($scope.old_password, $scope.new_password);
	}
	

})

app.controller("AdminCtrl", function($scope, $http) {

	console.log("Now in the admin ctrl2!");
	$scope.recentUsers = [];

	$scope.searchInput = "";

	$scope.selectedUserName = ""
	$scope.selectedUserID = -1;
	$scope.selectedUserJobCount = "";
	$scope.selectedUserIsAdmin = false
	$scope.selectedUserIsPrivaleged = false
	$scope.privalegedButtonText = "Make Privaleged";
	$scope.adminButtonText = "Make Admin";
	$scope.message = ""

	$scope.getRecentUsers = function(){
		$http({
			method: 'GET',
			url: '/admin/recentlyaddedusers'
		}).then(function successCallback(response){
			$scope.recentUsers = response.data;
			$scope.getUserInfo(response.data[0]);		
		});
	}

	$scope.getUserInfo = function(userID){
		$http({
			method: "GET",
			url: '/admin/getUserInfo/' + userID
		}).then(function successCallback(response){
			console.log(response)
			$scope.selectedUserName = userID
			$scope.selectedUserJobCount = response.data[0]
			$scope.selectedUserIsAdmin = response.data[1]
			$scope.selectedUserIsPrivaleged = response.data[2]
		})
	}

	$scope.getSelectedID = function(){
		$http({
			method: "GET",
			url: '/admin/getUserID/' + $scope.selectedUserName
		}).then(function successCallback(response){
			$scope.selectedUserID = response.data[0]
			console.log($scope.selectedUserID)
			return response.data[0]
		})
	}

	$scope.searchUser = function(){
		console.log("Search Pressed")
		console.log($scope.searchInput)
		$scope.getUserInfo($scope.searchInput)
	}

	$scope.selectRecentUser = function(userName){
		$scope.getUserInfo(userName)
	}

	$scope.promoteToAdmin = function(){
		$http({
			method: "GET",
			url: '/admin/promoteToAdmin/' + $scope.selectedUserName
		}).then(function successCallback(response){
			$scope.message = response.data
		})
	}

	$scope.promoteToPrivaleged = function(){
		$http({
			method: "GET",
			url: '/admin/promoteToPrivaleged/' + $scope.selectedUserName
		}).then(function successCallback(response){
			$scope.message = response.data
		})
	}

	$scope.getRecentUsers();

})

app.controller("JobCtrl", function($scope, $location, $timeout, JobService) {
	console.log("Now loading job...");
	$scope.job = {};
	$scope.job.name = "";

	$scope.viewing_job_uuid = $location.absUrl().split("/").pop();

	JobService.getJob($scope.viewing_job_uuid, function(data) {
		console.log("DATA!:", data);
		$scope.job = data;
	})

	$scope.startAnalysis = function() {

		console.log("Starting analysis now...");

		JobService.startAnalysisForJob($scope.viewing_job_uuid, function(success, analysisId) {
			if(success) {
				console.log("started analysis!");

				$timeout(function() {
					$scope.job.analysisJobId = analysisId
				}, 1000)
			} else {
				console.log("Failed to create analysis!");
			}
		})

	}

})


app.controller("JobsCtrl", function($scope, JobsService) {

	$scope.jobs = [];

	JobsService.getJobs(function(jobs) {
		$scope.jobs = jobs;
	})

	$scope.cancelJob = function(job){
		var request = new XMLHttpRequest();
		request.open("POST", "/cancel_job");
		request.setRequestHeader("Content-Type", "application/json;charset=UTF-8");

		var payload = {};
		payload["jobId"] = job.uuid


		request.send(JSON.stringify(payload));

		request.onload = function() {
			console.log(request.response);
			job.status = "Completed"
		}
	}

	$scope.deleteJob = function(job){
		var request = new XMLHttpRequest();
		request.open("POST", "/delete_job");
		request.setRequestHeader("Content-Type", "application/json;charset=UTF-8");

		var payload = {};
		payload["jobId"] = job.uuid


		request.send(JSON.stringify(payload));

		request.onload = function() {
			console.log(request.response);
			job.status = "Deleted"
		}
	}

	$scope.confirmDelete = function(job) {
		var r = confirm("Are you sure you want to delete job " + job.name + ".\nAll files related to this job will no longer be available.");
		if (r == true) {
		  $scope.deleteJob(job);
		} 
	  }

})

app.controller("LoginCtrl", function($scope) {
})

app.controller("MainCtrl", function($scope, $http) {

	$scope.data = {};
	$scope.error = "";

	$scope.auxillary = {
		"temperature":20,
		"temperature_units":"celsius",
		"mismatch_repulsion":"false"
	}

	$scope.parseData = function() {

		//convert all boolean values from strings to actual booleans
		for(key in $scope.auxillary) {
			var value = $scope.auxillary[key];
			if(key === "false") {
				$scope.data[key] = false;
			}
			if(key === "true") {
				$scope.data[key] = true;
			}
		}

		//convert temperature from segmented representation to one string like "100C"
		var temperature_ending = $scope.auxillary.temperature_units == "celsius" ? "C" : "K"
		var temperature_string = $scope.auxillary.temperature + temperature_ending;


		$scope.data["T"] = temperature_string;

	}

	$scope.setDefaults = function() {
		$scope.data["job_title"] = "My Job"
		$scope.data["steps" ] = 1e9;
		$scope.data["salt_concentration"] = 1.0;
		$scope.data["backend"] = "CPU";
		$scope.data["interaction_type"]= "DNA";
		$scope.data["print_conf_interval"] = 5e5;
		$scope.data["print_energy_every"] = 5e4;
	}

	$scope.parseData();
	$scope.setDefaults();


	$scope.hasSubmitted = false


	$scope.postJob = function() {

		//At this point
		//all data has been parsed, files have been read into a JSON bundle
		//and is sent to the server

		var request = new XMLHttpRequest();
		request.open("POST", "/create_job");
		request.setRequestHeader("Content-Type", "application/json;charset=UTF-8");

		var payload = {};
		payload["files"] = $scope.data["files"];
		delete $scope.data["files"];
		payload["parameters"] = $scope.data;

		request.send(JSON.stringify(payload));

		request.onload = function() {
			if(request.response == "Success") {
				window.location = "/jobs";
				console.log("Job submission was a success!")
			} else {
				$scope.error = request.response;
				$scope.$apply();

				console.log("Error set?:", $scope.error)
			}
			console.log(request.response);
			//window.location = "/jobs"
		}
	}

	$scope.submitJob = function() {
		$scope.parseData()
		TriggerFileDownloads();


		var file_data = {};

		var fullyRead = 0;

		for(fileName in files) {
			var reader = new FileReader();
 			reader.onloadend = (function(fileName) {
 				return function(event) {
 					var read_data = event.target.result;
 					file_data[fileName] = read_data;
 					fullyRead++;
 					readCallback();
 				}
 			})(fileName);
 			reader.readAsText(files[fileName])
		}

		var readCallback = function() {
			if(fullyRead == 2) {
				$scope.data["files"] = file_data;
				$scope.postJob()
			}
		}
	}
})