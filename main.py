from fastapi import FastAPI, HTTPException
from sqlalchemy import create_engine, text
import pandas as pd
from sqlalchemy.orm import sessionmaker
from pydantic import BaseModel

# FastAPI app instance
app = FastAPI()

# Setup database connection (PostgreSQL)
DATABASE_URL = "postgresql://flightsdatabase_xl0d_user:gLL0c9sOa0eIV4R620leC0eUpbpwBUNt@dpg-cvpchsmuk2gs739i9b5g-a.oregon-postgres.render.com/flightsdatabase_xl0d"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Helper function to execute a raw SQL query
def execute_sql_query(query: str):
    try:
        with SessionLocal() as session:
            df = pd.read_sql(query, con=session.bind)
            return df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Pydantic model for SQL query
class SQLQuery(BaseModel):
    query: str

@app.post("/data/execute_sql")
def execute_sql(query: SQLQuery):
    try:
        data = execute_sql_query(query.query)
        return data
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to execute SQL query: {str(e)}")

# ✅ New route: Fetch data from specific table
@app.get("/data/{table_name}")
def get_table_data(table_name: str):
    try:
        with SessionLocal() as session:
            query = text(f"SELECT * FROM {table_name} LIMIT 1000")  # optional: limit rows
            df = pd.read_sql(query, con=session.bind)
            return df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Table `{table_name}` not found or error: {str(e)}")
