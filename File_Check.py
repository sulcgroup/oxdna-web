import sys
import os
from ast import literal_eval
from time import time
from copy import deepcopy

import EmailScript
from Account import getUsername
from Job import getJobNameForUuid

# Purpose: Delete or notify user of large files that are too old by searching the user directory
# INPUTS (all optional):
    # dir = directory to begin searching, default "/users"
    # size_limit = files smaller will be ignored, bytes
    # warning_time = files older will be sent to user in a warning email, seconds
    # deletion_time = files older will be deleted if the user has been warned, seconds
    # output_dir = directory for output files, default is dir or "/users" if dir is missing
    # -d = flag for debug mode, files will not be deleted
# OUTPUT
    # Results dictionary of the following form: {user id: ([warning files], [])}
    # The second empty list is temp storage during execution; it holds files to be deleted
# EXAMPLE COMMAND:
    # python File_Check.py /users 100000 432000 604800 results -d

DEFAULT_SIZE_LIMIT = 1000000 # 1MB
DEFAULT_WARNING_TIME = 432000 # five days
DEFAULT_DELETION_TIME = 604800 # one week
DEFAULT_DIR = "/users"
OUTPUT_FILE = "results.txt"
CURRENT_TIME = time()

def main(dir, size_limit, warning_time, deletion_time, output_dir, debug):
    output_path = os.path.join(output_dir, OUTPUT_FILE)

    # create new results.txt if running for the first time (or in different directory)
    if OUTPUT_FILE in os.listdir(output_dir):
        print("Updating results.txt...")
        file = open(output_path, "r")
        try:
            old_results = literal_eval(file.read())
        except SyntaxError:
            print("Failure: Can't read results.txt. Please delete it and run again.")
            exit(0)
    else:
        print("Creating new output file...")
        file = open(output_path, "w")
        old_results = {}

    file.close()
    results = deepcopy(old_results)

    searchDirectory(dir, results, size_limit, warning_time, deletion_time)

    # results.txt contains a dict where keys are userIds and values are tuples ([warning_files list], [deletion_files list]).
    # warning_files is replaced by new files for emailing users and possible deletion next time the script is run
    for user in results.keys():
        files_tuple = results[user]
        warning_files = files_tuple[0]
        deletion_files = files_tuple[1]
        email_warning_files = []
        email_deletion_files = []

        email = getUsername(user)
        url = "http://localhost:9000/jobs"

        # format job files for warning
        for job_path in warning_files:
            job_path_list = job_path.split('/')
            job_name = getJobNameForUuid(job_path_list[0])
            job_file = job_path_list[-1]
            email_warning_files.append("{}: {}".format(job_name, job_file))
        # send warning email
        if email_warning_files and not debug:
            email_warning_files = ', '.join(email_warning_files)
            EmailScript.SendEmail("-t``4``-n``{username}``-u``{url}``-d``{email}``-j``{files}".format(username = email, url = url, email = email, files = email_warning_files).split("``"))

        # format job files for deletion & delete the files
        for job_path in deletion_files:
            job_path_list = job_path.split('/')
            job_name = getJobNameForUuid(job_path_list[0])
            job_file = job_path_list[-1]
            email_deletion_files.append("{}: {}".format(job_name, job_file))

            path_to_job = os.path.join(dir, str(user), job_path)
            if os.path.exists(path_to_job):
                if not debug:
                    os.remove(path_to_job)
            else:
                print("Failure: tried to remove job that doesn't exist")
                exit(0)
        # send deletion email
        if email_deletion_files and not debug:
            email_deletion_files = ', '.join(email_deletion_files)
            EmailScript.SendEmail("-t``5``-n``{username}``-d``{email}``-j``{files}".format(username = email, email = email, files = email_deletion_files).split("``"))
    
    # update warning files in results with old results dctionary only if the file hasn't been deleted
    for user in old_results.keys():
        new_results = []
        for file in old_results[user][0]:
            if not file in results[user][1]:
                new_results.append(file)

        results[user][0].extend(new_results)

    # remove deletion files from results dict
    for user in results.keys():
        results[user] = (results[user][0],[])

    file = open(output_path, "w")
    file.write(str(results))
    file.close()
    print("Success: File check complete!")
    return results

# Update results dictionary with jobs to be warned to the user and jobs to be deleted
def searchDirectory(dir, results, size_limit, warning_time, deletion_time):
    for item in os.listdir(dir):
        path = os.path.join(dir, item)

        # recursive case
        if os.path.isdir(path):
            searchDirectory(path, results, size_limit, warning_time, deletion_time)

        # base case - check job file stats
        else:
            if item == OUTPUT_FILE:
                continue

            path_list = path.split('/')
            # job files can't be in the /users, id, or job directory levels
            if len(path_list) < 5:
                print("Failed: There is a file where there shouldn't be.")
                exit(0)

            file_stats = os.stat(path)
            size = file_stats.st_size
            elapsed_time = CURRENT_TIME - file_stats.st_mtime

            # handle large & old file
            if size > size_limit and elapsed_time > warning_time:
                user = int(path_list[2])
                try:
                    warning_files = results[user][0]
                except KeyError:
                    warning_files = []
                    results.update({ user: ([],[])})
                deletion_files = results[user][1]
                problem_file = '/'.join(path_list[3:])

                # core logic of the script
                if elapsed_time > deletion_time and problem_file in warning_files:
                    warning_files.remove(problem_file)
                    deletion_files.append(problem_file)
                elif not problem_file in warning_files:
                    warning_files.append(problem_file)
                else:
                    warning_files.remove(problem_file)

                results.update({ user: (warning_files, deletion_files) })


size_limit = DEFAULT_SIZE_LIMIT
warning_time = DEFAULT_WARNING_TIME
deletion_time = DEFAULT_DELETION_TIME
dir = output_dir = DEFAULT_DIR
debug = False

args = len(sys.argv)

# Input validation
# sys.argv[0] = script name, no need to validate
if args > 1:
    try:
        dir = output_dir = sys.argv[1]
    except:
        print("Failed: First argument invalid. Try \"/users\".")
    if not os.path.isdir(dir):
        print("Failed: First argument is not a directory. Try \"/users\".")
        exit(0)

if args > 2:
    try:
        size_limit = int(sys.argv[2])
    except:
        print("Failed: Second argument invalid, represents size limit in bytes.")
        exit(0)

if args > 3:
    try:
        warning_time = int(sys.argv[3])
    except:
        print("Failed: Third argument invalid, represents warning time in seconds.")
        exit(0)

if args > 4:
    try:
        deletion_time = int(sys.argv[4])
    except:
        print("Failed: Fourth argument invalid, represents deletion time in seconds.")
        exit(0)

if args > 5:
    try:
        output_dir = sys.argv[4]
    except:
        print("Failed: Fifth argument invalid. Try \"/users\".")
        exit(0)
    if not os.path.isdir(output_dir):
        print("Failed: Fifth argument not a directory. Try \"/users\".")
        exit(0)

if args > 5:
    debug = True if "-d" in sys.argv[5] else False

if warning_time > deletion_time:
    print("Failed: Warning time cannot be greater than the deletion time.")
    exit(0)

main(dir, size_limit, warning_time, deletion_time, output_dir, debug)
exit(0)
