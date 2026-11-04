from contextlib import asynccontextmanager  #Handles startup and shutdown
from fastapi import FastAPI #Creates our API application
from app import database  # Imports our database connection functions.
from app.routes import auth, departments, doctors, patients, appointments

@asynccontextmanager
async def lifespan(app: FastAPI):#Asynchronous context manager that handles the startup and shutdown of the API application.

    await database.connect_db() # Creates a connection pool to the PostgreSQL database when the API application starts up
    yield # This is where the API application will run 
    await database.close_db() # Closes the database connection when the API application shuts down

app = FastAPI(
    title = "Hospital management system API",
    description = "This API is used to manage hospital data, including patients, doctors, and appointments.",
    version = "1.0.0", 
    lifespan = lifespan
)

app.include_router(auth.router)
app.include_router(departments.router)
app.include_router(doctors.router)
app.include_router(patients.router)
app.include_router(appointments.router)

@app.get("/")
async def home (): # Creares  a GET endpoint at the root URL ("/") of the API application.
    return {"Message": "Welcome to the Hospital Management System API!"} # sends a JSON response 


@app.get("/health") #Creates a health-check API.
async def health_check(): # Creates a GET endpoint at the "/health" URL of the API

    result = await database.pool.fetchval("SELECT 1") #Executes SQL and returns a single value.

    return {
        "Status": "Healthy",
        "Database": "Connected" if result == 1 else "Disconnected"
    } 

