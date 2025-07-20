import json
import psycopg2
from geojson import Feature, FeatureCollection

def get_outbreaks():
    # Connect to PostgreSQL inside the function
    conn = psycopg2.connect(
        dbname="postgres",  
        user="postgres",
        password="your_password",
        host="127.0.0.1"
    )
    
    cur = conn.cursor()
    cur.execute("""
        SELECT ST_AsGeoJSON(location), severity 
        FROM outbreaks
    """)
    
    # Create and return FeatureCollection
    features = [
        Feature(
            geometry=json.loads(row[0]), 
            properties={"severity": row[1]}
        ) 
        for row in cur.fetchall()
    ]
    
    conn.close()  # Don't forget to close the connection!
    return FeatureCollection(features)

# Test
if __name__ == "__main__":
    print(get_outbreaks())