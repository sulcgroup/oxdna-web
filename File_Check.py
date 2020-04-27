import sys
import os
from datetime import datetime
import mysql.connector

#external python script/modules
from Account import getEmail, getUsername
from Job import getJobForUserId


#cnx = mysql.connector.connect(user='root', password='', database='azdna')
#cursor = cnx.cursor()

#find_username_by_id_query = ("SELECT username FROM Users WHERE id = %s")

#def getUsername(userId):
#    cursor.execute(find_username_by_id_query(userId))
#    return cursor.username

def isHex(string):
    try:
        int(string, 16)
        return True
    except ValueError:
        return False


DEFAULT_SIZE_LIMIT = 1024 #One kilobyte
DEFAULT_TIME_LIMIT = 432000  #five days, notification threshold.
DELETION_TIME_LIMIT = 604800 #one week, deletion threshold.

OUTPUT_FILE_NAME = "results.txt"


class User:
    def __init__(self, mum, path):
        self.num = num
        self.files = []
        self.deletedfiles = []
        self.path = str(path)




#function to recursively search directories.
#INPUTS:
    #dir - path to target directory to search
    #offending_users - list of users (integer id) who have problem files
    #user - the user for which files in the current directory belong to
    #size_limit - size_limit in bytes
    #time_limit - time_limit in bytes
#OUTPUT:
    #dirsize - size of the directory specified by input dir in bytes.

def SearchDirectory(dir, results, size_limit, time_limit, user, offending_users, DELETE_TIME, DEBUG):
    pwd = os.path.basename(os.path.normpath(dir))
    #check if the current directory matches a user id
    if(str(pwd).isdigit()):
        #if so, all files and subdirectories belong to this user
        user = User(int(pwd), dir)
        offending_users.append(user)
    #variable to keep track of directory size.
    dirsize = 0;
    #get the current time
    currentdt = datetime.now()
    #iterate through each item in the current directory
    for x in os.listdir(dir):
        path = os.path.join(dir,x)
        #check if an item is a directory
        if(os.path.isdir(path)):
            #if so, search that directory recursively. (this is equivalent to depth first search)
            dirsize += SearchDirectory(path, results, size_limit, time_limit, user, DELETE_TIME, DEBUG)
        else:
            #if the item is a file.
            #get its statistics
            filestats = os.stat(path)
            fsize = filestats.st_size
            dirsize += fsize
            #calculate time since last modified
            filedt = datetime.fromtimestamp(filestats.st_atime)
            lastmodified = currentdt - filedt
            #check if the size or time modified exceed the limit
            if (lastmodified.total_seconds() > time_limit and fsize > size_limit):
                #results[1].append(str(path))
                #check if the file is old enough to be deleted
                if(lastmodified.total_seconds() > DELETE_TIME):
                    #delete the file and keep track of the name to notify user.
                    if(not DEBUG):
                        os.remove(path) #test to make sure everything works properly in a virtual machine before release.

                    if(not user is None):
                        user.deletedfiles.append(str(path))

                #issue the user a warning.
                elif(not user is None):
                    user.files.append(str(path))
    #outside loop
    if(dirsize > size_limit):
        #results[0].append(str(path))
        pass
    #check if the user has offending files and if so, add them to the list if they haven't been
    if(not user is None and (not user.files.isempty() or user.deletedfiles.isempty()) and not user in offending_users):
        offending_users.append(user)
    return dirsize

size_limit = DEFAULT_SIZE_LIMIT
time_limit = DEFAULT_TIME_LIMIT

#check for valid command line arguments.

#first command line argument is root directory to begin searching from.
#item in sys.argv[0] is the script itself
if(len(sys.argv) < 2):
    print("No directory specified")
    exit(0)

try:
    root = sys.argv[1]
    outputdir = root
except IndexError:
    print("Please specify root directory to begin search")
    exit(0)

if(not os.path.isdir(sys.argv[1])):
    print("Argument not a directory")
    exit(0)

if(len(sys.argv) > 2):
    try:
        size_limit = int(sys.argv[2])
    except:
        print("Second argument not an integer, represents size in bytes")
        exit(0)

if(len(sys.argv) > 3):
    try:
        time_limit = int(sys.argv[3])
    except:
        print("Third argument not integer, represents time in seconds")
        exit(0)

if(len(sys.argv) > 4):
    outputdir = sys.argv[4]

if(len(sys.argv) > 5):
    cmd = sys.argv[5]
    if("-d" in cmd):
        DEBUG = True
    else:
        DEBUG = False

try:
    outputfile = open(os.path.join(outputdir, OUTPUT_FILE_NAME), 'w')
except:
    print("unable to open output file")
    exit(0)

results = []

SearchDirectory(root, results, size_limit, time_limit, None, results, DELETION_TIME_LIMIT, DEBUG)


for i in results:
    #get user information
    username = getUsername(i.num)
    user_email = getEmail(i.num)
    #remove the path to user directory from file paths
    files = [filename.replace(i.path, "") for filename in i.files]
    deletedfiles = [filename.replace(i.path, "") for filename in i.deletedfiles]
    filestring = ""
    deletedfilestring = ""
    #replace job uuids with their names, and construct file list for emailing script
    for record in files:
        subdirs = record.split("\\")
        for subdir in subdirs:
            if(len(subdir) == 36 and isHex(subdir)):
                jobname = getJobForUserId(subdir).get("name")
                record.replace(subdir, jobname)
        filestring = filestring + "\n" + record
    #same thing as above but for the deleted files.
    for record in deletedfiles:
        subdirs = record.split("\\")
        for subdir in subdirs:
            if(len(subdir) == 36 and isHex(subdir)):
                jobname = getJobForUserId(subdir).get("name")
                record.replace(subdir, jobname)
        deletedfilestring = deletedfilestring + "\n" + record

    #construct access url
    domain_name = "www.oxdna.org"
    url = domain_name + "/jobs"

    # call emailing script, assuming it is in the same directory
    if(filestring):
        os.system("python3 /vagrant/azDNA/EmailScript.py -t 4 -n " + username + " -u " + url + " -d " + user_email + " -l " + filestring)
    if(deletedfilestring):
        os.system("python3 /vagrant/azDNA/EmailScript.py -t 4 -n " + username + " -d " + user_email + " -l " + deletedfilestring)

    if(DEBUG):
        for (file in i.files):
            outpufile.write(file)
            outpufile.write("\r\n")
        for (file in i.deletedfiles):
            outpufile.write(file)
            outpufile.write("\r\n")
    #print(files)
    #print(deletedfiles)


outputfile.close()
exit(0)

