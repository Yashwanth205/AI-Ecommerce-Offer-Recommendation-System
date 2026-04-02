from supabase import create_client
import os

# -------------------------------
# Supabase Config
# -------------------------------
SUPABASE_URL = "https://foxqakvkvtrqlxgmymwc.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhzeWl3aHVrc21uemtwZmV6dnhuIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQzMTEyNTMsImV4cCI6MjA4OTg4NzI1M30.A7XOs-uKHJoH4sLMYjXEJ-AB361JBZHYbfm4DfXllSI"   

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


# -------------------------------
# Register User
# -------------------------------
def register_user(email, password):
    try:
        res = supabase.auth.sign_up({
            "email": email,
            "password": password
        })

        return res

    except Exception as e:
        print("Register Error:", e)
        return None


# -------------------------------
# Validate Login
# -------------------------------
def validate_user(email, password):
    try:
        res = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })

        if res.user:
            return True

        return False

    except Exception as e:
        print("Login Error:", e)
        return False


# -------------------------------
# (Optional) Get User Info
# -------------------------------
def get_user(email):
    try:
        res = supabase.auth.admin.list_users()

        for user in res:
            if user.email == email:
                return user

    except Exception as e:
        print("Get User Error:", e)

    return None