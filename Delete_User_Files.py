import os
import sys
import shutil

DIRECTORY = '/users'

# remove user from the /users directory
def deleteUser(user_id):
    users = os.listdir(DIRECTORY)

    for user in users:
        if user == user_id:
            path_to_user = os.path.join(DIRECTORY, user)
            shutil.rmtree(path_to_user)
