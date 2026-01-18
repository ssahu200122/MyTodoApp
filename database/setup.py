from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# 1. The Database File
# This will create 'todo_app.db' in the main folder
DB_FILE = 'sqlite:///todo_app.db'

# 2. The Engine (The Ignition)
# echo=False stops it from printing SQL logs to console (cleaner output)
engine = create_engine(DB_FILE, echo=False)

# 3. The Session Factory
# We use this to create a new "Staging Area" whenever we need one
SessionLocal = sessionmaker(bind=engine)

# 4. The Base (The Blueprint)
# All our models will inherit from this
Base = declarative_base()

# 5. Helper function to initialize the DB
def init_db():
    # This checks our models and creates the tables if they don't exist
    Base.metadata.create_all(engine)