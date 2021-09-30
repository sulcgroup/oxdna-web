import subprocess
import sys
import os
import re
import argparse
from ast import literal_eval
from time import time
from copy import deepcopy

import EmailScript
from Account import getUsername, getEmailPrefs
from Job import getJobNameForUuid


# Purpose: Notify users, delete large & old files by searching the user directory
# OPTIONS (all optional):
    # -d = directory to search, default /users
    # -s = size limit in bytes, files smaller will be ignored
    # -w = warning time in seconds, files older will be sent to user in a warning email
    # -x = deletion time in seconds, files older will be deleted if the user has been warned
    # -o = output directory for results.txt, default /users
    # -b = flag for debug mode, files will not be deleted
# OUTPUT
    # Results dictionary of the following form: {user id: ([warning files], [])}
    # The second empty list is temp storage during execution; it holds files to be deleted
# EXAMPLE COMMAND:
    # python File_Check.py -d /users -s 100000 -w 432000 -x 604800 -o results -b


DEFAULT_SIZE_LIMIT = 5000000 # 5MB
DEFAULT_WARNING_TIME = 432000 # five days
DEFAULT_DELETION_TIME = 604800 # one week
DEFAULT_DIR = "/users"
OUTPUT_FILE = "results.txt"
CURRENT_TIME = time()

def is_dir(dir):
    if os.path.isdir(dir):
        return dir
    raise argparse.ArgumentTypeError("Must be a valid directory")


def main(dir, size_limit, warning_time, deletion_time, output_dir, debug):
    output_path = os.path.join(output_dir, OUTPUT_FILE)

    # create new results.txt if running for the first time (or in different directory)
    if OUTPUT_FILE in os.listdir(output_dir):
        f = open(output_path, "r")
        try:
            old_results = literal_eval(f.read())
            if not isinstance(old_results, dict):
                print("Failure: Contents of results.txt must be a dictionary. Please delete it and run again.")
                f.close()
                exit(0)
        except:
            print("Failure: Can't read results.txt. Please delete it and run again.")
            f.close()
            exit(0)
        print("Updating results.txt...")
    else:
        f = open(output_path, "w")
        old_results = {}
        print("Creating new output file...")

    f.close()
    results = deepcopy(old_results)

    searchDirectory(dir, results, size_limit, warning_time, deletion_time)

    # results.txt contains a dict where keys are userIds and values are tuples ([warning_files list], [deletion_files list]).
    # warning_files is replaced by new files for emailing users and possible deletion next time the script is run
    bad_emails = []
    for user in results.keys():
        files_tuple = results[user]
        warning_files = files_tuple[0]
        deletion_files = files_tuple[1]
        email_warning_files = []
        email_deletion_files = []

        url = "https://oxdna.org/jobs"
        email = getUsername(user)
        email_prefs = getEmailPrefs(user)
        
        if not "@" in email:
            print(email, " is not a valid email. User ", user, " will not be notified.")
            bad_emails.append(email)
            continue
        
        # format job files for warning
        for job_path in warning_files:
            job_path_list = job_path.split('/')
            job_name = getJobNameForUuid(job_path_list[0])
            job_file = job_path_list[-1]
            email_warning_files.append("{}: {}".format(job_name, job_file))
                
        # send warning email
        if email_warning_files and email_prefs[2] == '1' and not debug:
            email_warning_files = ',\n'.join(email_warning_files)
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
        if email_deletion_files and email_prefs[4] == '1' and not debug:
            email_deletion_files = ',\n'.join(email_deletion_files)
            EmailScript.SendEmail("-t``5``-n``{username}``-d``{email}``-j``{files}".format(username = email, email = email, files = email_deletion_files).split("``"))
    
    # update warning files in results with old results dictionary only if the file hasn't been deleted
    for user in old_results.keys():
        new_results = []
        for file in old_results[user][0]:
            if not (file in results[user][1]):
                new_results.append(file)

        results[user][0].extend(new_results)

    # remove duplicates and deletion files
    for user in results.keys():
        results[user] = (list(set(results[user][0])), [])
        
    file = open(output_path, "w")
    file.write(str(results))
    file.close()
    print("Success: File check complete!")
    if bad_emails:
        print("The following emails are not valid and were not notified: ", bad_emails)
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

                # core logic of script
                if elapsed_time > deletion_time and problem_file in warning_files:
                    warning_files.remove(problem_file)
                    deletion_files.append(problem_file)
                elif not problem_file in warning_files:
                    warning_files.append(problem_file)
                else:
                    warning_files.remove(problem_file)

                results.update({ user: (warning_files, deletion_files) })


# parse command line arguments
parser = argparse.ArgumentParser(description='Notify users, delete large & old files by searching the user directory.')

parser.add_argument('-d', metavar='dir', type=is_dir, nargs=1, default=DEFAULT_DIR, help='directory to search, default {}'.format(DEFAULT_DIR))
parser.add_argument('-s', metavar='size_limit', type=int, nargs=1, default=DEFAULT_SIZE_LIMIT, help='in bytes, files smaller will be ignored, default {}'.format(DEFAULT_SIZE_LIMIT))
parser.add_argument('-w', metavar='warning_time', type=int, nargs=1, default=DEFAULT_WARNING_TIME, help='in seconds, files older will be sent to user in a warning email, default {}'.format(DEFAULT_WARNING_TIME))
parser.add_argument('-x', metavar='deletion_time', type=int, nargs=1, default=DEFAULT_DELETION_TIME, help='in seconds, files older will be deleted if the user has been warned. default {}'.format(DEFAULT_DELETION_TIME))
parser.add_argument('-o', metavar='output_dir', type=is_dir, nargs=1, default=DEFAULT_DIR, help='directory for output files, default is dir or "/users" if dir is missing. default {}'.format(DEFAULT_DIR))
parser.add_argument('-b', action='store_true', help='debug mode, files will not be deleted, emails will not be sent, default False')

args = parser.parse_args()

dir = args.d[0] if isinstance(args.d, list) else args.d
size_limit = args.s[0] if isinstance(args.s, list) else args.s
warning_time = args.w[0] if isinstance(args.w, list) else args.w
deletion_time = args.x[0] if isinstance(args.x, list) else args.x
output_dir = args.o[0] if isinstance(args.o, list) else args.o
debug = args.b[0] if isinstance(args.b, list) else args.b


# execute script
main(dir, size_limit, warning_time, deletion_time, output_dir, debug)
exit(0)
