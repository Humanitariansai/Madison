"""
Setup database - creates database and tables if they don't exist
Run this after PostgreSQL is running
"""
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from src.config import load_env
from src.database import engine, Base
from src.models import User, FileHistory, ReportHistory

def setup_database():
    """Create database and tables"""
    env = load_env()
    
    # Get connection details
    db_user = env.get("DB_USER", "postgres")
    db_password = env.get("DB_PASSWORD", "postgres")
    db_host = env.get("DB_HOST", "localhost")
    db_port = env.get("DB_PORT", "5432")
    db_name = env.get("DB_NAME", "survey_analysis")
    
    print(f"Connecting to PostgreSQL at {db_host}:{db_port}...")
    
    try:
        # Connect to postgres database to create our database
        conn = psycopg2.connect(
            host=db_host,
            port=db_port,
            user=db_user,
            password=db_password,
            database="postgres"  # Connect to default postgres database
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        
        # Check if database exists
        cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
        exists = cur.fetchone()
        
        if not exists:
            print(f"Creating database '{db_name}'...")
            cur.execute(f'CREATE DATABASE "{db_name}"')
            print(f"✓ Database '{db_name}' created successfully!")
        else:
            print(f"✓ Database '{db_name}' already exists")
        
        cur.close()
        conn.close()
        
        # Now create tables in the database
        print(f"\nCreating tables in '{db_name}'...")
        Base.metadata.create_all(bind=engine)
        print("✓ Tables created successfully!")
        print("\nDatabase setup complete! You can now use the application.")
        
    except psycopg2.OperationalError as e:
        print(f"\n❌ Error connecting to PostgreSQL:")
        print(f"   {e}")
        print("\nMake sure:")
        print("  1. PostgreSQL is running (check Docker containers)")
        print("  2. Port 5432 is accessible")
        print("  3. Credentials in .env file are correct")
        return False
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    setup_database()

