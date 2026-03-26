# 🌍 Vex: Disease Outbreak Mapping API

Vex is a FastAPI backend for real-time disease outbreak visualization, primarily focused on Africa. It queries a PostgreSQL/PostGIS database for outbreak locations, severity levels, and detection dates, serving data as GeoJSON FeatureCollections for frontend mapping (Google Maps, pydeck, or Streamlit).

**Key Functionality**:
- Fetch outbreak data as interactive GeoJSON heatmaps.
- Supports CORS for easy frontend integration.
- Serves static frontend files from `/frontend`.

## 🔥 Features
- **/outbreaks endpoint**: Returns GeoJSON with geometry (points/polygons), severity (e.g., low/medium/high), and timestamps.
- **CORS-enabled**: Works with any frontend origin (adjust for production).
- **Static file serving**: Mounts frontend at root `/`.
- **Extensible**: Ready for AI predictions (Vertex AI/LSTM via deps like openai, kaggle datasets).

## 🏗️ How It Works
1. **Database**: PostgreSQL + PostGIS stores outbreaks in `outbreaks` table:
   ```sql
   -- Inferred schema
   CREATE TABLE outbreaks (
       id SERIAL PRIMARY KEY,
       location GEOMETRY(POINT, 4326),
       severity VARCHAR(20),
       detected_at TIMESTAMP
   );
   ```
2. **API Flow**:
   - `GET /outbreaks` → Queries `ST_AsGeoJSON(location)`, builds FeatureCollection.
   - Returns: `{"type": "FeatureCollection", "features": [...]}`.
3. **Frontend**: Place HTML/JS in `frontend/`; access via server root.
4. **AI-Ready**: Dependencies include ML tools; extend with LSTM models trained on health data (e.g., Kaggle datasets).

**Example Response**:
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {"type": "Point", "coordinates": [32.5, -1.9]},
      "properties": {"severity": "high", "date": "2024-01-15T10:00:00"}
    }
  ]
}
```

## 🛠️ Tech Stack
- **Backend**: FastAPI, Uvicorn
- **Database**: PostgreSQL + PostGIS (psycopg2)
- **Data/ML**: pandas, numpy, streamlit, pydeck, openai, kaggle
- **Mapping**: GeoJSON (ST_AsGeoJSON)
- **Other**: CORS, static files

## 🚀 Setup & Installation

### 1. Prerequisites
- Python 3.10+
- PostgreSQL 15+ with PostGIS extension
- Google Cloud account (optional, for future Vertex AI)

### 2. Clone & Environment
```bash
# Current dir is project root
cd c:/Users/admin/desktop/vex
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r backend/requirements.txt
```

### 3. Database Setup
```bash
# Create DB & enable PostGIS (psql or pgAdmin)
CREATE DATABASE vex_outbreaks;
\c vex_outbreaks
CREATE EXTENSION postgis;

-- Create table
CREATE TABLE outbreaks (
    id SERIAL PRIMARY KEY,
    location GEOMETRY(POINT, 4326),
    severity VARCHAR(20),
    detected_at TIMESTAMP DEFAULT NOW()
);

-- Sample data (Africa outbreaks)
INSERT INTO outbreaks (location, severity) VALUES
(ST_SetSRID(ST_MakePoint(32.58, 0.31), 4326), 'high'),  -- Uganda
(ST_SetSRID(ST_MakePoint(-1.29, 36.82), 4326), 'medium'); -- Kenya
```

**Update DB Credentials**: Edit `backend/app.py` and `backend/map_outbreaks.py`:
- Replace hardcoded `password="your_password"`, `dbname`, etc.
- Better: Use `python-dotenv` for `.env` file (add to reqs if needed).

### 4. Run the Server
```bash
uvicorn backend.app:app --host 0.0.0.0 --port 8000 --reload
```
- Visit `http://localhost:8000` → Health check.
- `http://localhost:8000/outbreaks` → GeoJSON data.
- Open frontend: Place `index.html` in `frontend/`, access at `/`.

### 5. Frontend Example
Create `frontend/index.html`:
```html
<!DOCTYPE html>
<html>
<head>
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
</head>
<body>
    <div id="map" style="height: 500px;"></div>
    <script>
        fetch('/outbreaks').then(r => r.json()).then(data => {
            const map = L.map('map').setView([5, 20], 3);
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);
            L.geoJSON(data).addTo(map);
        });
    </script>
</body>
</html>
```

## 🔧 Development & Next Steps
- **Populate DB**: Use Kaggle health datasets.
- **AI Integration**: Add `/predict` endpoint with Vertex AI LSTM.
- **Secure**: Env vars for DB, HTTPS in prod.
- **Deploy**: Dockerize, Railway/Heroku/Vercel.
- **Tests**: Add pytest for endpoints/DB queries.

## 📄 License
MIT

Questions? Check code or open issues.

