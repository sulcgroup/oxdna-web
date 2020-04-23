import codecs
import yagmail
import sys


#get help text and email credentials
try:
    EMAIL_CREDENTIALS = open("AZDNALogin.txt", "r").read().split(";")
    HELP_TEXT = open("EmailScriptHelp.txt", "r").read()
except FileNotFoundError:
    print("Error, Login File not found")

#subject lines for templates

#initialize email sever
yag = yagmail.SMTP(EMAIL_CREDENTIALS[0], EMAIL_CREDENTIALS[1])

def SendEmail(args):


    argdict = {}

    currentargs = None
    try:
        for arg in args:
            if(arg[0] == "-"):
                #check if we already have a list of these argments
                if(argdict.get(arg[1:], None)):
                    currentargs = argdict.get(arg[1:])
                else:
                    argdict[arg[1:]] = []
                    currentargs = argdict[arg[1:]]
            else:
                currentargs.append(arg)

    except AttributeError:
        print("Error, argument passed before flag")
        exit(0)

    if(not argdict.get("d", None)):
        print("Error, destination email address not specified")
        exit(0)
    try:
        #parse the desired template number
        template_num = int(argdict.get("t")[0])
    except AttributeError:
        print("Error, template number not specified")
        exit(0)
    except ValueError:
        print("Error, invalid template number")
        exit(0)

    #open the templates file and get the right template
    with open("AZDNA_Email_Templates.txt", "r") as file:
        #templates separated by double semicolons
        templates = file.read().split(";;")
        #header and footers are the first two template items
        header = templates[0]
        footer = templates[1]
        #remaining templates
        templates = templates[2:]
        #get the desired template
        try:
            #Subject line is first line, separated by body by double colons, so body is teh second element in the split
            subject = templates[template_num].split("::")[0]
            template = templates[template_num].split("::")[1]

        except IndexError:
            print("Error, invalid template number")
            exit(0)
        #put in the header and footer
        template = template.replace("<HEADER>", header)
        template = template.replace("<TAIL>", footer)
        #insert the arguments
        for argtype, arglist in argdict.items():
            #construct the argument template string to be repalced
            replacestr = "<" + argtype + ">"
            #iterate through the available arguments.
            for arg in arglist:
                arg = arg.replace("_", " ")
                #replace arguments one at a time
                template = template.replace(replacestr, arg, 1)
        #resolve any escape characters
        template = codecs.decode(template, 'unicode_escape')
        #send the email
        mailtosend = [template]
        #print(mailtosend[0])
        subject = subject.replace("\n", "")
        subject = codecs.decode(subject, 'unicode_escape')
        yag.send(argdict.get("d")[0], subject, mailtosend)

#parse arguments
if("-h" in sys.argv):
    print(HELP_TEXT)
    exit(0)

if("EmailScript.py" in sys.argv):
    args = sys.argv[1:]
    SendEmail(args)
