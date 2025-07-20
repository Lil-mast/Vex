from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware  # For frontend connectivity
from map_outbreaks import get_outbreaks
from geojson import FeatureCollection
import psycopg2
import json

# Initialize FastAPI
app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"])

# Allow CORS for frontend (critical for local development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production!
    allow_methods=["GET"],
    allow_headers=["*"],
)

# Database connection function
def get_db_connection():
    return psycopg2.connect(
        dbname="vex_outbreaks",  # Your database name
        user="postgres",         # PostgreSQL username
        password="your_password", # Your PostgreSQL password
        host="localhost"         # Or "127.0.0.1"
    )

# Fetch outbreaks as GeoJSON
def fetch_outbreaks():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT 
            ST_AsGeoJSON(location) AS geometry,
            severity,
            detected_at
        FROM outbreaks
    """)
    features = [
        {
            "type": "Feature",
            "geometry": json.loads(row[0]),
            "properties": {
                "severity": row[1],
                "date": row[2].isoformat()
            }
        }
        for row in cur.fetchall()
    ]
    conn.close()
    return FeatureCollection(features)

# API endpoint
@app.get("/outbreaks")
def get_outbreaks():
    return fetch_outbreaks()

# Serve frontend (optional)
from fastapi.staticfiles import StaticFiles
app.mount("/", StaticFiles(directory="../frontend", name="static"))

# Test route
@app.get("/")
def read_root():
    return {"message": "Vex Outbreak Detection API is running!"}