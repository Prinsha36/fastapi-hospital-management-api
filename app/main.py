from contextlib import asynccontextmanager  #Handles startup and shutdown
from pathlib import Path
from fastapi import FastAPI #Creates our API application
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from app import database  # Imports our database connection functions.
from app.routes import auth, departments, doctors, patients, appointments, emergency, gemini

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
app.include_router(emergency.router)
app.include_router(gemini.router)

app.mount(
    "/ui",
    StaticFiles(directory=Path(__file__).resolve().parents[1] / "frontend", html=True),
    name="frontend",
)


@app.get("/test-ui", include_in_schema=False)
@app.get("/test-ui/", include_in_schema=False)
async def legacy_test_ui():
    return RedirectResponse("/ui/#emergency", status_code=307)


class HomeOut(BaseModel):
    Message: str


class HealthOut(BaseModel):
    Status: str
    Database: str


@app.get("/", response_model=HomeOut)
async def home (): # Creares  a GET endpoint at the root URL ("/") of the API application.
    return {"Message": "Welcome to the Hospital Management System API!"} # sends a JSON response 


@app.get("/health", response_model=HealthOut) #Creates a health-check API.
async def health_check(): # Creates a GET endpoint at the "/health" URL of the API

    result = await database.pool.fetchval("SELECT 1") #Executes SQL and returns a single value.

    return {
        "Status": "Healthy",
        "Database": "Connected" if result == 1 else "Disconnected"
    } 

