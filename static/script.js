var app = angular.module("app", [])


app.controller("JobsCtrl", function($scope, $http) {

	$scope.jobs = [];

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
		$scope.jobs = data;
	});

})

app.controller("MainCtrl", function($scope, $http) {

	$scope.data = {};

	$scope.auxillary = {
		"temperature":334,
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
		$scope.data["steps" ] = 1000;
		$scope.data["salt_concentration"] = 0.5;
		$scope.data["backend"] = "CPU";
		$scope.data["interaction_type"]= "DNA";
		$scope.data["print_conf_interval"] = 10;
		$scope.data["print_energy_every"] = 10;
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
			window.location = "/jobs"
			console.log("Job submission was a success!")
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