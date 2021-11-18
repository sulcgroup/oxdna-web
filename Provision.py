import Register
import Admin

user = {
    "email" : "admin",
    "password" : "password",
    "firstName" : "admin",
    "lastName" : "admin",
    "institution" : "Admin University",
    "iAgree" : True
}
Register.registerUser(user, requires_verification=False)
Admin.promoteToAdmin(1)