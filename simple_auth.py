from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta
import jwt
from pymongo import MongoClient

app = FastAPI()

# Secret key for JWT (change this in production!)
SECRET_KEY = "your-secret-key-here"

# MongoDB Connection
MONGO_URI = "mongodb+srv://user:password123@cluster0.mongodb.net/auth_db?retryWrites=true&w=majority"
# Alternative for local MongoDB:
# MONGO_URI = "mongodb://localhost:27017"

client = MongoClient(MONGO_URI)
db = client["auth_db"]
users_collection = db["users"]

# Create default users if they don't exist
default_users = [
    {"email": "user@example.com", "password": "password123"},
    {"email": "admin@example.com", "password": "admin123"},
]

for user in default_users:
    existing = users_collection.find_one({"email": user["email"]})
    if not existing:
        users_collection.insert_one(user)

# Models
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    message: str

# Login endpoint
@app.post("/login", response_model=LoginResponse)
def login(data: LoginRequest):
    email = data.email
    password = data.password
    
    # Check if user exists in MongoDB
    user = users_collection.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Check password
    if user["password"] != password:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Create JWT token
    payload = {
        "email": email,
        "exp": datetime.utcnow() + timedelta(hours=24)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "message": "Login successful!"
    }

# Signup endpoint (optional)
@app.post("/signup")
def signup(data: LoginRequest):
    email = data.email
    password = data.password
    
    # Check if user already exists in MongoDB
    existing = users_collection.find_one({"email": email})
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")
    
    # Add new user to MongoDB
    users_collection.insert_one({"email": email, "password": password})
    
    return {"message": "User created successfully!", "email": email}

# Test endpoint
@app.get("/")
def home():
    return {"message": "Simple Login API", "test_email": "user@example.com", "test_password": "password123"}
