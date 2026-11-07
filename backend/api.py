from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from . import data_model
BASE = Path(__file__).resolve().parent.parent
app = FastAPI(title="Data Center Thermal Digital Twin API", version="0.3.0")
@app.get("/api/health")
def health(): return {"status":"ok","version":"0.3.0","data_mode":"synthetic-demo"}
@app.get("/api/metadata")
def metadata(): return data_model.metadata()
@app.get("/api/frame/{frame_index}")
def frame(frame_index:int):
    try: return data_model.frame_data(frame_index)
    except IndexError as e: raise HTTPException(404,str(e)) from e
@app.get("/api/series/{sensor_id}")
def series(sensor_id:str):
    try: return data_model.sensor_series(sensor_id)
    except KeyError as e: raise HTTPException(404,f"Unknown sensor: {sensor_id}") from e
@app.get("/",include_in_schema=False)
def index(): return FileResponse(BASE/"frontend/index.html")
app.mount("/assets",StaticFiles(directory=BASE/"frontend"),name="assets")
