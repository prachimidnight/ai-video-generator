import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

# We use the DATABASE_URL environment variable if present
DATABASE_URL = os.getenv("DATABASE_URL", "mongodb://localhost:27017/social_stamp")

client = MongoClient(DATABASE_URL)

# If the connection string specifies a database (e.g. at the end of the URI), use that.
# Otherwise, default to "social_stamp"
db_name = "social_stamp"
try:
    if client.get_default_database().name:
        db_name = client.get_default_database().name
except Exception:
    pass

database = client[db_name]

# Dependency to get db session
def get_db():
    try:
        yield database
    finally:
        pass
