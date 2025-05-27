import streamlit as st
import pandas as pd

# Set up the page
st.set_page_config(page_title="Brewery Fermentation Dashboard", layout="wide")

# 1) Load the one Master CSV containing the last 4 weeks of data
csv_url = st.secrets["master_csv"]
data = pd.read_csv(csv_url)

# 2) Parse dates and flag packaging rows
data["DateFerm"] = pd.to_datetime(data["DateFerm"], errors="coerce")
data["is_packaging"] = data["What_are_you_filling_out_today_"] == "Packaging Data"

# 3) Find latest record per fermenter
latest = (
    data.sort_values("DateFerm")
        .groupby("Daily_Tank_Data.FVFerm", as_index=False)
        .last()
)

# 4) Title
st.title("🍺 Brewery Fermentation Dashboard")

# 5) Display live metrics for each FV
cols = st.columns(len(latest))
for idx, row in latest.iterrows():
    fv = row["Daily_Tank_Data.FVFerm"]
    with cols[idx]:
        st.metric(label=fv, value=f"{row['Daily_Tank_Data.GravityFerm']} °P")
        st.write(f"pH: {row['Daily_Tank_Data.pHFerm']}")
        stage = row["Daily_Tank_Data.What_Stage_in_the_Product_in_"]
        st.write(f"Stage: *{stage}*")
        if row["is_packaging"]:
            st.error("📦 Packaging entry detected")

# 6) Plot gravity over time for a selected FV
fv_choice = st.selectbox(
    "Select fermenter to view gravity curve",
    sorted(data["Daily_Tank_Data.FVFerm"].dropna().unique())
)
df_fv = data[data["Daily_Tank_Data.FVFerm"] == fv_choice].set_index("DateFerm")
st.line_chart(df_fv["Daily_Tank_Data.GravityFerm"])
