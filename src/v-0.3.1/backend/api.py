
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
import math

BASE = Path(__file__).resolve().parents[1]

app = FastAPI(
    title="AI Data Center Thermal Twin",
    version="0.3.1"
)

ROOM = {
    "length": 12.0,
    "width": 8.0,
    "height": 3.5
}

# Procedural rack generation: no CAD
RACKS = []

for row in range(2):
    for col in range(5):

        idx = row * 5 + col

        RACKS.append({
            "id": f"R{idx+1:02d}",
            "x": 1.35 + col * 2.25,
            "y": 1.65 if row == 0 else 6.35,
            "z": 0.0,
            "width": 0.6,
            "depth": 1.2,
            "height": 2.0,
            "row": row + 1
        })


# 36 temperature sensors
SENSORS = []

sid = 1

for rack_i, rack in enumerate(RACKS):

    levels = (
        [0.35, 0.95, 1.55, 1.85]
        if rack_i < 6
        else [0.45, 1.15, 1.8]
    )

    for level in levels:

        SENSORS.append({
            "id": f"T{sid:02d}",
            "rack_id": rack["id"],
            "x": rack["x"],
            "y": rack["y"] - 0.68,
            "z": level
        })

        sid += 1


TIMESTEPS = 48


def generate_frame(t):

    t = max(0, min(TIMESTEPS - 1, t))

    phase = 2 * math.pi * t / TIMESTEPS

    values = []

    for i, s in enumerate(SENSORS):

        rack_num = int(s["rack_id"][1:])

        base = 22.5 + 1.6 * math.sin(
            phase - 0.6
        )

        hot_aisle = 3.0 * math.exp(
            -((s["y"] - 3.8) / 1.35) ** 2
        )

        vertical = 1.4 * s["z"] / ROOM["height"]

        rack_load = 1.1 * (
            0.5 + 0.5 * math.sin(
                rack_num * 0.9 + phase * 1.3
            )
        )

        local = 0.35 * math.sin(
            i * 1.7 + phase * 2
        )

        temperature = round(
            base + hot_aisle +
            vertical + rack_load + local,
            2
        )

        airflow = round(
            0.55 + 0.35 * (
                0.5 + 0.5 * math.cos(
                    phase + rack_num
                )
            ),
            2
        )

        values.append({
            **s,
            "temperature": temperature,
            "airflow": airflow
        })

    return {
        "version": "0.3.1",
        "timestep": t,
        "minutes": t * 5,
        "timestamp": f"T+{t*5:03d} min",
        "room": ROOM,
        "racks": RACKS,
        "sensors": values
    }


@app.get("/api/health")
def health():

    return {
        "status": "ok",
        "version": "0.3.1",
        "cad_required": False
    }


@app.get("/api/config")
def config():

    return {
        "room": ROOM,
        "racks": RACKS,
        "sensor_count": len(SENSORS),
        "timesteps": TIMESTEPS,
        "interval_minutes": 5
    }


@app.get("/api/frame/{t}")
def frame(t: int):

    return generate_frame(t)


@app.get("/")
def index():

    return FileResponse(
        BASE / "frontend" / "index.html"
    )


app.mount(
    "/static",
    StaticFiles(directory=BASE / "frontend"),
    name="static"
)

