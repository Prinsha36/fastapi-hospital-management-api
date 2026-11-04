import asyncpg   # A python library used to connect python application to PostgreSQL database asynchronously
import os   #Reads environment variables.
from dotenv import load_dotenv # Loads variables from the .env file.

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")  # Reads the database URL value  from  the .env file.
pool = None  # stires the database connection pool. initially, its value is  None. Because  no connection has been created yet.

async def connect_db():  #This function creates a connection pool to the PostgreSQL database using the asyncpg library.
    global pool # Declares the pool variable as global, so that it can be accessed and modified within the function.

    pool = await asyncpg.create_pool(DATABASE_URL,min_size=2, max_size=10) # Creates a connection pool to the PostgreSQL database using the DATABASE_URL.
    print("Database connected successfully")

async def close_db():
    global pool 
    await pool.close()
    print("Database connection closed successfully!")

