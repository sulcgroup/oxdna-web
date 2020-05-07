import Register
import Admin

Register.registerUser(name="admin", password="admin", firstName="admin", lastName="admin", institution="Admin University", requires_verification=False)
Admin.promoteToAdmin(1)