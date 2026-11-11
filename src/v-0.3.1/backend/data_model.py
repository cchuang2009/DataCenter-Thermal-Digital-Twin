"""Synthetic demo dataset. API coordinates: X=width, Y=depth, Z=height."""
from math import sin, cos, pi, exp
ROOM = {"width": 10.0, "depth": 7.0, "height": 3.2}
RACKS = [{"id": f"R{i+1:02d}", "x": x, "y": y, "width": .72, "depth": 1.05, "height": 2.1}
         for i, (x,y) in enumerate([(x,y) for y in (1.1,3.15) for x in (1.05,2.05,3.05,4.05,5.05)])]
SENSORS = []
for r in RACKS:
    cx = r["x"] + r["width"]/2
    for level,z in enumerate((.45,1.15,1.85),1):
        SENSORS += [
          {"id":f'{r["id"]}-F{level}',"x":round(cx,3),"y":round(r["y"]-.18,3),"z":z,"kind":"rack-inlet"},
          {"id":f'{r["id"]}-B{level}',"x":round(cx,3),"y":round(r["y"]+r["depth"]+.18,3),"z":z,"kind":"rack-outlet"}]
for i,(x,y,z) in enumerate([(.35,.35,.5),(9.5,.35,.5),(.35,6.6,.5),(9.5,6.6,.5),(.35,.35,2.7),(9.5,.35,2.7)],1):
    SENSORS.append({"id":f"ROOM-{i:02d}","x":x,"y":y,"z":z,"kind":"room-reference"})
FRAME_COUNT, INTERVAL_MINUTES = 48, 5

def temperature(s, frame):
    cycle = .5 + .5*sin(2*pi*frame/(FRAME_COUNT-1)-.8)
    base = 29.0 if s["kind"] == "rack-outlet" else 22.2
    return round(base + 2.2*cycle + .7*s["z"]/ROOM["height"]
                 + exp(-((s["x"]-3.5)**2)/5) + .35*cos(s["y"]*pi/ROOM["depth"])
                 + .22*sin(frame*.22+s["x"]*.7+s["z"]), 2)

def velocity(s, frame):
    p = frame*.12+s["x"]*.3
    return {"x":round(.08*sin(p),3),"y":round(.55+.12*cos(p+s["y"])+(0.18 if s["kind"]=="rack-outlet" else 0),3),
            "z":round(.04*sin(p*.7)+(0.08 if s["kind"]=="rack-outlet" else 0),3)}

def metadata():
    return {"project":"Data Center Thermal Digital Twin","version":"0.3.0","data_mode":"synthetic-demo",
      "data_notice":"Synthetic demo values, not Aalborg measurements.","room":ROOM,"frame_count":FRAME_COUNT,
      "interval_minutes":INTERVAL_MINUTES,"sensor_count":len(SENSORS),"rack_count":len(RACKS),
      "coordinate_convention":"X=width, Y=depth, Z=height; origin=front-left-floor.",
      "sensors":SENSORS,"racks":RACKS}

def frame_data(i):
    if not 0 <= i < FRAME_COUNT: raise IndexError(f"frame_index must be 0..{FRAME_COUNT-1}")
    return {"frame_index":i,"elapsed_minutes":i*INTERVAL_MINUTES,"timestamp_label":f"T+{i*INTERVAL_MINUTES:03d} min",
      "readings":[{**s,"temperature_c":temperature(s,i),"air_velocity_m_s":velocity(s,i)} for s in SENSORS]}

def sensor_series(sensor_id):
    s = next((s for s in SENSORS if s["id"]==sensor_id),None)
    if s is None: raise KeyError(sensor_id)
    return {"sensor":s,"series":[{"frame_index":i,"elapsed_minutes":i*INTERVAL_MINUTES,"temperature_c":temperature(s,i)} for i in range(FRAME_COUNT)]}
