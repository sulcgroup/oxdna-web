import os
import time
import uuid
import subprocess
import mysql.connector

cnx = mysql.connector.connect(user='root', password='', database='azdna')
cursor = cnx.cursor()

find_email_by_user_id_query = ("SELECT email FROM UsersDev WHERE id = %s")
set_email = ("UPDATE UsersDev SET email = %s WHERE id = %s")
find_date_by_user_id_query = ("SELECT creationDate FROM UsersDev WHERE id = %s")
find_status_by_user_id_query = ("SELECT status FROM UsersDev WHERE id = %s")
get_verify_code_query = ("SELECT verifycode FROM UsersDev WHERE id = %s")
verify_user = ("UPDATE UsersDev SET verified = %s WHERE id = %s")
get_username_query = ("SELECT username FROM UsersDev WHERE id = %s")
get_userid_query = ("SELECT id FROM UsersDev WHERE username = %s")


##DEPRECATED
def getEmail(userId):
    cursor.execute(find_email_by_user_id_query(userId))
    return cursor.email

def setEmail(email, userId):
    cursor.execute(set_email(email, userId))
    return "Email successfully updated!"
##DEPRECATED

def getCreationDate(userId):
    cursor.execute(find_date_by_user_id_query, (userId,))
    #fetchall returns all results
    results = cursor.fetchall()
    if(results):
        return results[0][0]
    else:
        return None

def getStatus(userId):
    cursor.execute(find_status_by_user_id_query, (userId,))
    #fetchall returns all results
    results = cursor.fetchall()
    if(results):
        return results[0][0]
    else:
        return None

def getVerificationCode(userId):
    cursor.execute(get_verify_code_query, (userId,))
    #fetchall returns all results
    results = cursor.fetchall()
    if(results):
        return results[0][0]
    else:
        return None

def getUsername(userId):
    cursor.execute(get_username_query, (userId,))
    #fetchall returns all results
    results = cursor.fetchall()
    if(results):
        return results[0][0]
    else:
        return None

def getUserId(username):
    cursor.execute(get_userid_query, (username,))
    #fetchall returns all results
    results = cursor.fetchall()
    if(results):
        return results[0][0]
    else:
        return None


#checks verification code for user
def verifyUser(userId, VerifyCode):
    #not sure how mysql.connector works, so wrapping in try catch just in case
    try:
        #query the database for the user's verification code
        cursor.execute(get_verify_code_query, (userId,))
        code = cursor.fetchall()
        #check that they match
        if(code[0][0] == VerifyCode):
            #verify the user
            cursor.execute(verify_user, ("True", userId))
            cnx.commit()
            return True;
        else:
            return False;
    except:
        return False;
