from pathlib import Path
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from src.loader import load_preview, to_long, guess_col

st.set_page_config(page_title="DataCenter Thermal Digital Twin v0.2", layout="wide")
st.title("DataCenter Thermal Digital Twin · v0.2")
st.caption("Aalborg measured-data spatial twin prototype. Measured sensor points are shown separately from any future interpolation.")
data_dir=Path("data")
csv_files=sorted(data_dir.glob("*.csv"))
xlsx_files=sorted(data_dir.glob("*.xlsx"))

st.sidebar.header("1 · Data")
uploaded=st.sidebar.file_uploader("Upload temperature/power CSV",type=["csv"])
local_options=["— choose —"]+[p.name for p in csv_files]
chosen=st.sidebar.selectbox("Local CSV",local_options)
if uploaded:
    df=pd.read_csv(uploaded,nrows=250000,low_memory=False)
    source=uploaded.name
elif chosen!="— choose —":
    df=load_preview(data_dir/chosen)
    source=chosen
else:
    df=None; source=None

if df is None:
    st.info("Download the Aalborg dataset into ./data, or upload its temperature/power CSV.")
    st.markdown("[Aalborg latest record](https://zenodo.org/records/21262042) · [Aalborg v4](https://zenodo.org/records/19398358)")
    st.stop()

st.subheader("2 · Data schema and field mapping")
st.write(f"Source: `{source}` · Preview rows: {len(df):,} · columns: {len(df.columns)}")
st.dataframe(df.head(8),use_container_width=True)
cols=list(df.columns)
numeric=list(df.select_dtypes(include=np.number).columns)
time_guess=guess_col(cols,["timestamp","datetime","date","time"]) or cols[0]
temp_guess=guess_col(numeric,["temperature","temp","t_air"]) or (numeric[0] if numeric else None)
sensor_guess=guess_col(cols,["sensor_id","measurement_point","point_id","sensor","probe"])
time_col=st.selectbox("Time column",cols,index=cols.index(time_guess))
sensor_mode=st.radio("CSV structure",["Wide: one column per sensor","Long: sensor ID column + temperature column"],horizontal=True)
if sensor_mode.startswith("Long"):
    sensor_col=st.selectbox("Sensor ID column",cols,index=cols.index(sensor_guess) if sensor_guess in cols else 0)
    temp_col=st.selectbox("Temperature column",numeric,index=numeric.index(temp_guess) if temp_guess in numeric else 0)
else:
    sensor_col=None
    sensor_cols=st.multiselect("Sensor temperature columns (select one or more)",numeric,default=numeric[:min(12,len(numeric))])
    temp_col=None

st.subheader("3 · Sensor to XYZ mapping")
mapping_path=st.sidebar.file_uploader("Upload reviewed sensor_xyz_template.csv",type=["csv"])
default_map=Path("outputs/inspection/sensor_xyz_template.csv")
if mapping_path:
    mapping=pd.read_csv(mapping_path)
elif default_map.exists():
    mapping=pd.read_csv(default_map)
else:
    mapping=pd.DataFrame(columns=["sensor_id","measurement_port","x_m","y_m","z_m","coordinate_source","review_status"])
if len(mapping):
    for c in ["x_m","y_m","z_m"]:
        if c in mapping: mapping[c]=pd.to_numeric(mapping[c],errors="coerce")
    mapping["sensor_id"]=mapping["sensor_id"].astype(str).str.strip()
    valid=mapping.dropna(subset=["x_m","y_m","z_m"]).copy()
    st.write(f"Mapping rows: {len(mapping)} · rows with complete XYZ: {len(valid)}")
    st.dataframe(mapping.head(15),use_container_width=True)
else:
    valid=mapping
    st.warning("No sensor coordinate mapping found. Run the inspector, then fill XYZ coordinates from the official drawing and upload the reviewed CSV.")
if not len(valid):
    st.stop()

st.subheader("4 · 3D measured temperature points")
if sensor_mode.startswith("Long"):
    long=to_long(df,time_col,temp_col,sensor_col)
else:
    if not sensor_cols:
        st.warning("Select at least one sensor column."); st.stop()
    long=df[[time_col]+sensor_cols].melt(id_vars=[time_col],var_name="sensor_id",value_name="temperature")
    long=long.rename(columns={time_col:"timestamp"})
    long["sensor_id"]=long["sensor_id"].astype(str)
    long["temperature"]=pd.to_numeric(long["temperature"],errors="coerce")
    long=long.dropna(subset=["temperature"])
long["timestamp"]=long["timestamp"].astype(str)
# Keep a limited number of time stamps in the UI
times=long["timestamp"].drop_duplicates().tolist()
if len(times)>500:
    stride=max(1,len(times)//500)
    times=times[::stride]
selected_time=st.selectbox("Measurement time",times)
slice_df=long[long["timestamp"]==selected_time]
plot_df=slice_df.merge(valid,on="sensor_id",how="inner")
if plot_df.empty:
    st.error("No sensor IDs matched the XYZ map at this time. Check exact IDs, port mapping, and CSV structure.")
    st.write("CSV sensor ID examples:",long["sensor_id"].drop_duplicates().head(20).tolist())
    st.write("XYZ map ID examples:",valid["sensor_id"].head(20).tolist())
    st.stop()
fig=px.scatter_3d(plot_df,x="x_m",y="y_m",z="z_m",color="temperature",
                  hover_name="sensor_id",hover_data=["temperature","coordinate_source","review_status"],
                  color_continuous_scale="Turbo",title="Measured air-temperature values at verified sensor coordinates")
fig.update_traces(marker=dict(size=5))
fig.update_layout(scene=dict(xaxis_title="X (m)",yaxis_title="Y (m)",zaxis_title="Z (m)"))
st.plotly_chart(fig,use_container_width=True)
st.caption("Each marker is a measured sensor location. No unmeasured volume is coloured or represented as observed data.")
st.metric("Matched measured sensors",len(plot_df))
st.dataframe(plot_df[["sensor_id","x_m","y_m","z_m","temperature","coordinate_source","review_status"]],use_container_width=True)

st.subheader("5 · Export matched measurement snapshot")
csv_bytes=plot_df.to_csv(index=False).encode("utf-8")
st.download_button("Download this timestamp's matched 3D points (CSV)",csv_bytes,
                   file_name="aalborg_3d_temperature_points.csv",mime="text/csv")
