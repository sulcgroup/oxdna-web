def getBufferedTrajectoryForUserJobIdAtOffset(user_id, job_id, offset, amount):

	file = open("jobfiles/"+str(user_id)+"/"+job_id+"/"+"trajectory.dat")

	counter = 1
	traj_lengths = None

	line = file.readline()
	offsets = []

	while line != "":
		if line[:3] == "t =":
			print(file.tell())
			offsets.append(file.tell())

			if traj_lengths is None and counter is not 1:
				traj_lengths = counter-1

		line = file.readline()
		counter += 1

	offset_time = offsets[offset]
	last_time = offsets[offset+amount]

	file.seek(max(0,offset_time-7-1))
	dat = file.read(last_time-offset_time)

	for i in range(1, len(offsets)):
		print(offsets[i]-offsets[i-1])

	#print(dat)

getBufferedTrajectoryForUserJobIdAtOffset(1, "57a4b416-a949-4c2b-9e0b-a04cec37075f", 1, 2)