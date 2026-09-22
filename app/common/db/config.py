import os

from dotenv import load_dotenv

load_dotenv()

def get_database_url() -> str:
    # Define the required environment variables
    required_vars = [
        "DATABASE_HOST",
        "DATABASE_PORT",
        "DATABASE_NAME",
        "DATABASE_USER",
        "DATABASE_PASSWORD"
    ]
    
    # Identify any variables that are completely missing or empty string/whitespace
    missing_vars = [
        var for var in required_vars 
        if not os.getenv(var) or os.getenv(var).strip() == ""
    ]
    
    if missing_vars:
        raise EnvironmentError(
            f"Missing required database configuration environment variables: "
            f"{', '.join(missing_vars)}"
        )

    # Fetch values safely knowing they are guaranteed to exist and have content
    host = os.getenv("DATABASE_HOST")
    port = os.getenv("DATABASE_PORT")
    name = os.getenv("DATABASE_NAME")
    user = os.getenv("DATABASE_USER")
    password = os.getenv("DATABASE_PASSWORD")

    return f"postgresql+psycopg://{user}:{password}@{host}:{port}/{name}"
