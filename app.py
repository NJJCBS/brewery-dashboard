import streamlit as st
import pandas as pd
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import gspread
from datetime import datetime, timedelta

# --- 1. Auth via service account stored in Streamlit secrets ---
creds_info = st.secrets["gcp_service_account"]
scopes = [
    "https://www.googleapis.com/auth/drive.readonly",
    "https://www.googleapis.com/auth/spreadsheets.readonly",
]
creds = Credentials.from_service_account_info(creds_info, scopes=scopes)
drive = build("drive", "v3", credentials=creds)
gc = gspread.authorize(creds)

# --- 2. Parameters ---
FOLDER_ID = st.secrets["folder_id"]
DAYS = 21

# --- 3. List spreadsheets edited in last 21 days ---
cutoff = (datetime.utcnow() - timedelta(days=DAYS)).isoformat() + "Z"
query = (
    f"mimeType='application/vnd.google-apps.spreadsheet' "
    f"and '{FOLDER_ID}' in parents "
    f"and modifiedTime > '{cutoff}'"
)
resp = drive.files().list(q=query, fields="files(id,name,modifiedTime)").execute()
files = resp.get("files", [])

st.sidebar.markdown(f"**Found {len(files)} sheets** edited since {cutoff[:10]}")

# --- 4. Read & concatenate all sheets ---
all_records = []
for f in files:
    sh = gc.open_by_key(f["id"])
    ws = sh.get_worksheet(0)
    df = pd.DataFrame(ws.get_all_records())
    df["source_sheet"] = f["name"]
    all_records.append(df)
if not all_records:
    st.warning("No recent sheets to display.")
    st.stop()
data = pd.concat(all_records, ignore_index=True)

# --- 5. Preprocess & find latest per fermenter ---
data["DateFerm"] = pd.to_datetime(data["DateFerm"])
# flag packaging
data["is_packaging"] = data["What_are_you_filling_out_today_"] == "Packaging Data"
# pick latest per FV
latest = (data
    .sort_values("DateFerm")
    .groupby("Daily_Tank_Data.FVFerm")
    .tail(1)
    .set_index("Daily_Tank_Data.FVFerm")
)

# --- 6. Display metrics ---
st.title("🍺 Brewery Fermentation Dashboard")
cols = st.columns(len(latest))
for i, (fv, row) in enumerate(latest.iterrows()):
    with cols[i]:
        st.metric(fv, f"{row['Daily_Tank_Data.GravityFerm']} °P", delta=None)
        st.write(f"pH: {row['Daily_Tank_Data.pHFerm']}")
        stage = row["Daily_Tank_Data.What_Stage_in_the_Product_in_"]
        st.write(f"Stage: *{stage}*")
        if row["is_packaging"]:
            st.error("📦 Packaging data logged")

# --- 7. Plot gravity over time for a selected FV ---
fv_choice = st.selectbox("Choose a fermenter", sorted(data["Daily_Tank_Data.FVFerm"].unique()))
df_fv = data[data["Daily_Tank_Data.FVFerm"] == fv_choice]
st.line_chart(df_fv.set_index("DateFerm")["Daily_Tank_Data.GravityFerm"])
