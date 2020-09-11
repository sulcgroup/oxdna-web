# determine if we are in the server or the VM
def get_home_path():
    try:
    	open("/var/www/azDNA/azDNA/AZDNALogin.txt", "r")
    	path = "/var/www/azDNA/azDNA/"
    except FileNotFoundError:
    	path = "/vagrant/oxdna-web/"
    return path