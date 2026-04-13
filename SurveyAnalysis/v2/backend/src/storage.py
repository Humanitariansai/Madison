"""
Data storage utilities
"""
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
import pandas as pd
from pathlib import Path
from src.config import DB_PATH

def get_engine(db_path: Path = None) -> Engine:
    """Get database engine"""
    if db_path is None:
        db_path = DB_PATH
    return create_engine(f"sqlite:///{db_path}")

def save_processed(
    df: pd.DataFrame,
    engine: Engine,
    table_name: str = "responses",
    if_exists: str = "append"
):
    """Save processed dataframe to database"""
    df.to_sql(table_name, engine, if_exists=if_exists, index=False)

