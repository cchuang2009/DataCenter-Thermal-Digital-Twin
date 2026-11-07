# Data Center Thermal Digital Twin v0.3

[Aetifact on Render](https://datacenter-thermal-twin.onrender.com/)

To suit the Render's condition, link the backend, frentent, render.yaml,requirements.txt in src.

FastAPI + Three.js interactive 3D server-room demonstrator.

## Included
- 10 × 7 × 3.2 m synthetic room and 10 synthetic racks
- 66 synthetic temperature / airflow sensor points
- Temperature color mapping, orbit/zoom/pan and reset view
- Click sensors to inspect ID, XYZ, temperature and airflow speed
- Per-sensor temperature history chart
- 48-frame timeline, play/pause and airflow vector toggle
- FastAPI JSON API and Render Blueprint

## Data integrity warning
This release uses **synthetic demo values and synthetic positions only**. It is not the Aalborg University measured dataset, and sensor-to-CAD coordinates have not been verified. Do not use it for operational cooling decisions.

## Local run (Manjaro/Linux)
Python 3.11 or 3.12 recommended:
```bash
unzip DataCenter-Thermal-Digital-Twin-v0.3.zip
cd DataCenter-Thermal-Digital-Twin-v0.3
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
uvicorn backend.api:app --reload --host 127.0.0.1 --port 8000
```
Open http://127.0.0.1:8000 (API docs: `/docs`, health: `/api/health`). Three.js modules load from jsDelivr CDN, so the browser needs internet.

## Deploy to Render
1. Push this folder's contents to a GitHub repository.
2. In Render choose **New → Blueprint**, connect the repository containing `render.yaml`.
3. Review and deploy. Render serves the UI and API on one origin.
4. Open the generated `https://<service>.onrender.com` address.

Free services may spin down when inactive; the first request after sleep can be delayed. Free-tier storage is ephemeral. Check Render's current limits before relying on it.

## API endpoints
- `GET /api/health`
- `GET /api/metadata`
- `GET /api/frame/{frame_index}` (0–47)
- `GET /api/series/{sensor_id}`

## Coordinates
API convention: X=width, Y=depth, Z=height; origin at front-left-floor. Frontend maps API XYZ to Three.js XZY so the floor is the Three.js XZ plane.

## Next step for real data
Build a verified `sensor_id,x_m,y_m,z_m` coordinate table from the dataset workbook/CAD drawings. Join temperature records by sensor ID, not row order. Validate units, coordinate origin, room orientation and sensor identity before replacing the synthetic generator.
