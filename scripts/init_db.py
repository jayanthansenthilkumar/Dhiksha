"""
Database initialization script.
Creates tables, indexes, and partitions.
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from src.data.schemas import Base
from src.utils.config import settings


def create_tables(engine):
    """Create all tables defined in models."""
    print("Creating tables...")
    Base.metadata.create_all(engine)
    print("✅ Tables created")


def create_partitions(engine):
    """Create monthly partitions for events table (for production scale)."""
    print("Creating event table partitions...")
    
    with engine.connect() as conn:
        # Check if already partitioned
        result = conn.execute(text("""
            SELECT EXISTS (
                SELECT FROM pg_tables 
                WHERE tablename = 'events_2025_10'
            );
        """))
        
        if result.scalar():
            print("  Partitions already exist, skipping...")
            return
        
        # Convert events table to partitioned (if not already)
        # Note: In production, this should be part of migration
        conn.execute(text("""
            -- Create partitions for current and next 3 months
            CREATE TABLE IF NOT EXISTS events_2025_10 PARTITION OF events
            FOR VALUES FROM ('2025-10-01') TO ('2025-11-01');
            
            CREATE TABLE IF NOT EXISTS events_2025_11 PARTITION OF events
            FOR VALUES FROM ('2025-11-01') TO ('2025-12-01');
            
            CREATE TABLE IF NOT EXISTS events_2025_12 PARTITION OF events
            FOR VALUES FROM ('2025-12-01') TO ('2026-01-01');
            
            CREATE TABLE IF NOT EXISTS events_2026_01 PARTITION OF events
            FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');
        """))
        conn.commit()
    
    print("✅ Partitions created")


def create_mlflow_database(engine_url: str):
    """Create separate database for MLflow if it doesn't exist."""
    print("Setting up MLflow database...")
    
    # Connect to default 'postgres' database
    base_url = engine_url.rsplit('/', 1)[0]
    engine = create_engine(f"{base_url}/postgres")
    
    with engine.connect() as conn:
        conn.execution_options(isolation_level="AUTOCOMMIT")
        
        # Check if mlflow database exists
        result = conn.execute(text("SELECT 1 FROM pg_database WHERE datname = 'mlflow'"))
        if not result.scalar():
            conn.execute(text("CREATE DATABASE mlflow"))
            print("  ✅ MLflow database created")
        else:
            print("  MLflow database already exists")
    
    engine.dispose()


def create_prefect_database(engine_url: str):
    """Create separate database for Prefect if it doesn't exist."""
    print("Setting up Prefect database...")
    
    # Connect to default 'postgres' database
    base_url = engine_url.rsplit('/', 1)[0]
    engine = create_engine(f"{base_url}/postgres")
    
    with engine.connect() as conn:
        conn.execution_options(isolation_level="AUTOCOMMIT")
        
        # Check if prefect database exists
        result = conn.execute(text("SELECT 1 FROM pg_database WHERE datname = 'prefect'"))
        if not result.scalar():
            conn.execute(text("CREATE DATABASE prefect"))
            print("  ✅ Prefect database created")
        else:
            print("  Prefect database already exists")
    
    engine.dispose()


def create_extensions(engine):
    """Create PostgreSQL extensions (e.g., pg_stat_statements for query monitoring)."""
    print("Creating PostgreSQL extensions...")
    
    with engine.connect() as conn:
        conn.execution_options(isolation_level="AUTOCOMMIT")
        
        # pg_stat_statements for slow query analysis
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_stat_statements"))
        
        # uuid-ossp for UUID generation (backup to Python uuid4)
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\""))
    
    print("✅ Extensions created")


def verify_setup(engine):
    """Verify database setup."""
    print("Verifying database setup...")
    
    with engine.connect() as conn:
        # Check tables exist
        tables = ["users", "contents", "events", "model_versions", "recommendation_logs"]
        for table in tables:
            result = conn.execute(text(f"SELECT EXISTS (SELECT FROM pg_tables WHERE tablename = '{table}')"))
            if result.scalar():
                print(f"  ✅ Table '{table}' exists")
            else:
                print(f"  ❌ Table '{table}' missing!")
                return False
    
    print("✅ Database verification passed")
    return True


def main():
    print("=" * 60)
    print("Database Initialization Script")
    print("=" * 60)
    print()
    
    # Get database URL from environment or use default
    database_url = os.getenv(
        "DATABASE_URL",
        "postgresql://admin:localdev@localhost:5432/recommendations"
    )
    
    print(f"Database URL: {database_url.split('@')[1]}")  # Hide credentials
    print()
    
    # Create engine
    engine = create_engine(database_url, echo=False)
    
    try:
        # Test connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("✅ Database connection successful")
        print()
        
        # Create extensions
        create_extensions(engine)
        print()
        
        # Create tables
        create_tables(engine)
        print()
        
        # Create partitions (optional, for production scale)
        # Uncomment if you want partitioned events table
        # create_partitions(engine)
        # print()
        
        # Create MLflow database
        create_mlflow_database(database_url)
        print()
        
        # Create Prefect database
        create_prefect_database(database_url)
        print()
        
        # Verify setup
        if verify_setup(engine):
            print()
            print("=" * 60)
            print("✅ Database initialization completed successfully!")
            print("=" * 60)
            print()
            print("Next steps:")
            print("  1. Generate sample data: python scripts/sample_data_generator.py")
            print("  2. Start training models: python -m src.models.train_retrieval")
            return 0
        else:
            print()
            print("❌ Database verification failed!")
            return 1
    
    except Exception as e:
        print(f"\n❌ Error during database initialization: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    finally:
        engine.dispose()


if __name__ == "__main__":
    sys.exit(main())
