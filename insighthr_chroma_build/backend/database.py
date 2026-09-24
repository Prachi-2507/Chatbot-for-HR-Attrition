"""Load the bundled HR CSV into a local SQLite database."""

import os
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_CSV_PATH = BASE_DIR / "data" / "hr_attrition.csv"
DEFAULT_DB_PATH = BASE_DIR / "data" / "hr_attrition.db"
CSV_PATH = Path(os.getenv("HR_CSV_PATH", DEFAULT_CSV_PATH))
DB_PATH = Path(os.getenv("SQLITE_DB_PATH", DEFAULT_DB_PATH))
TABLE_NAME = "employees"


def build_database(csv_path: str | Path = CSV_PATH, db_path: str | Path = DB_PATH) -> str:
    """Read the HR CSV and load it into a SQLite table."""
    csv_path = Path(csv_path)
    db_path = Path(db_path)
    if not csv_path.exists():
        raise FileNotFoundError(f"HR dataset not found: {csv_path}")
    db_path.parent.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(csv_path)
    df.columns = [str(c).strip() for c in df.columns]

    engine = create_engine(f"sqlite:///{db_path}")
    df.to_sql(TABLE_NAME, engine, if_exists="replace", index=False)
    return f"sqlite:///{db_path}"


def get_connection_string(db_path: str | Path = DB_PATH) -> str:
    db_path = Path(db_path)
    if not db_path.exists():
        build_database()
    return f"sqlite:///{db_path}"


if __name__ == "__main__":
    conn_str = build_database()
    print(f"Database built at: {conn_str}")
    print(f"Table '{TABLE_NAME}' loaded successfully from {CSV_PATH}.")
