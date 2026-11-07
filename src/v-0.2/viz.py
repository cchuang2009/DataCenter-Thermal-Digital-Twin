import pandas as pd
import plotly.express as px

t = pd.read_csv("data/temperature.csv")
xyz = pd.read_csv("data/sensor_xyz.csv")

df = t.merge(
    xyz,
    on="Sensor_ID",
    how="left",
    validate="many_to_one"
)

if df[["X_m", "Y_m", "Z_m"]].isna().any().any():
    raise ValueError("有感測器尚未完成 XYZ 對應")

fig = px.scatter_3d(
    df,
    x="X_m",
    y="Y_m",
    z="Z_m",
    color="Temperature_C",
    hover_name="Sensor_ID",
    color_continuous_scale="Turbo"
)

