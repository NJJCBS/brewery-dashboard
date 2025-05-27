import streamlit as st
import pandas as pd
import plotly.express as px
from math import ceil

st.set_page_config(
    page_title="🍺 Brewery Fermentation Dashboard",
    layout="wide",
)

# --- 1) Load master CSV from Secrets ---
csv_url = st.secrets["master_csv"]
data = pd.read_csv(csv_url, parse_dates=["DateFerm"], dayfirst=True)

# --- 2) Clean & prepare ---
data = data.dropna(subset=["Daily_Tank_Data.FVFerm", "DateFerm"])
data["is_packaging"] = data["What_are_you_filling_out_today_"] == "Packaging Data"

# Find the latest row per fermenter
latest_idx = data.sort_values("DateFerm").groupby("Daily_Tank_Data.FVFerm")["DateFerm"].idxmax()
latest = data.loc[latest_idx].reset_index(drop=True)

# Get sorted fermenter list for consistent ordering
fermenters = latest["Daily_Tank_Data.FVFerm"].sort_values().tolist()

# --- 3) Helper to chunk list into pairs ---
def chunk(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i+n]

st.title("🍺 Brewery Fermentation Dashboard")

# --- 4) Render cards in rows of 2 ---
for row_fermenters in chunk(fermenters, 2):
    cols = st.columns(len(row_fermenters), gap="large")
    for col, fv in zip(cols, row_fermenters):
        # gather latest and full history for this FV
        row = latest[latest["Daily_Tank_Data.FVFerm"] == fv].iloc[0]
        hist = data[data["Daily_Tank_Data.FVFerm"] == fv].sort_values("DateFerm")
        
        with col:
            # Card container
            st.markdown(f"### **{fv}**")
            # You could also show Beer name if you have a column e.g. batch/style
            style = row.get("What_are_you_filling_out_today_", "")
            if style and style != "Packaging Data":
                st.caption(style.replace("_", " "))
            # Metrics
            st.write(f"**Gravity:** {row['Daily_Tank_Data.GravityFerm']} °P")
            st.write(f"**pH:** {row['Daily_Tank_Data.pHFerm']} pH")
            # Optional other metrics
            vol = row.get("Brewing_Day_Data.Volume_into_FV") or row.get("Transfer_Data.Final_Tank_Volume")
            if pd.notna(vol):
                st.write(f"**Volume:** {vol}")
            temp = row.get("Daily_Tank_Data.Actual_TemperatureFerm") or row.get("Daily_Tank_Data.Set_TemperatureFerm")
            if pd.notna(temp):
                st.write(f"**Temp:** {temp} °C")
            # Stage & packaging flag
            stage = row["Daily_Tank_Data.What_Stage_in_the_Product_in_"]
            st.write(f"**Stage:** *{stage}*")
            if row["is_packaging"]:
                st.error("📦 Packaging entry")
            # Mini line chart
            fig = px.line(
                hist,
                x="DateFerm",
                y="Daily_Tank_Data.GravityFerm",
                title=None
            )
            fig.update_layout(
                margin=dict(l=0, r=0, t=0, b=0),
                height=200,
                xaxis_title=None,
                yaxis_title=None,
                showlegend=False
            )
            fig.update_traces(line=dict(width=2))
            st.plotly_chart(fig, use_container_width=True)
