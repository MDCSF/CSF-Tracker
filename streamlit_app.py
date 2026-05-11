import streamlit as st
import pandas as pd
from datetime import date

st.set_page_config(page_title="CSF Action Dashboard", layout="wide")

@st.cache_data
def load_data():
    try:
        # Load data skipping the title row
        df = pd.read_csv('tracker_data.csv', skiprows=1)
        df.columns = df.columns.str.strip()
        
        # --- AGGRESSIVE PROGRESS EXTRACTION ---
        if 'Progress %' in df.columns:
            # 1. Convert to string and remove symbols like %, spaces, or commas
            df['Progress %'] = df['Progress %'].astype(str).str.replace('%', '').str.strip()
            
            # 2. Convert to actual numbers, turning errors into 0
            df['Progress %'] = pd.to_numeric(df['Progress %'], errors='coerce').fillna(0.0)
            
            # 3. Handle the "Whole vs Decimal" logic:
            # If the CSV has "75", we turn it into 0.75. If it has "1", it stays 1.0.
            # We only divide by 100 if the numbers are clearly whole numbers (greater than 1)
            if df['Progress %'].max() > 1.0:
                df['Progress %'] = df['Progress %'] / 100.0
        
        # --- DATE CLEANING ---
        if 'Deadline' in df.columns:
            df['Deadline'] = pd.to_datetime(df['Deadline'], errors='coerce').dt.date
            
        # --- COLUMN CLEANUP ---
        # Explicitly keep only the columns we want to avoid junk
        valid_cols = ['Task ID', 'Task Description', 'Owner', 'Priority', 'Deadline', 'Status', 'Progress %', 'Comments']
        # Only keep columns that actually exist in the file
        df = df[[c for c in valid_cols if c in df.columns]]
        
        return df
    except Exception as e:
        st.error(f"Data extraction error: {e}")
        return None

# Persist data in session
if 'main_df' not in st.session_state:
    st.session_state.main_df = load_data()

df = st.session_state.main_df

# --- HEALTH LOGIC ---
def get_health(row):
    today = date.today()
    deadline = row.get('Deadline')
    progress = row.get('Progress %', 0)
    status = str(row.get('Status', '')).strip()
    
    if status == 'Completed' or progress >= 1.0: return "🟢 Done"
    if pd.notnull(deadline) and deadline < today: return "🔴 OVERDUE"
    if pd.notnull(deadline) and (deadline - today).days <= 7: return "🟡 AT RISK"
    return "⚪ Pending"

df['Health'] = df.apply(get_health, axis=1)

# --- DASHBOARD ---
st.title("🚀 CSF Action Dashboard")

c1, c2, c3, c4 = st.columns(4)
overdue_df = df[df['Health'] == "🔴 OVERDUE"]
at_risk_df = df[df['Health'] == "🟡 AT RISK"]

c1.metric("Total Items", len(df))
c2.metric("🔴 Overdue", len(overdue_df))
c3.metric("🟡 At Risk", len(at_risk_df))
c4.metric("Avg. Progress", f"{int(df['Progress %'].mean() * 100)}%")

st.divider()

# Charts
l, r = st.columns(2)
with l:
    st.subheader("📊 Status Distribution")
    st.bar_chart(df['Status'].value_counts())
with r:
    st.subheader("⚠️ Red Alert: Who is Late?")
    if not overdue_df.empty:
        st.bar_chart(overdue_df.groupby('Owner').size())
    else:
        st.success("No overdue items. ✅")

# --- TABLE ---
st.subheader("📝 Master Action Tracker")
owners = sorted(df['Owner'].dropna().unique().tolist())
sel_owner = st.sidebar.multiselect("Filter Team Member", options=owners, default=owners)
f_df = df[df['Owner'].isin(sel_owner)]

edited_df = st.data_editor(
    f_df,
    num_rows="dynamic",
    use_container_width=True,
    hide_index=True,
    column_config={
        "Health": st.column_config.TextColumn("Health", width="small"),
        "Progress %": st.column_config.NumberColumn("Progress (%)", format="%.2f", min_value=0, max_value=1),
        "Deadline": st.column_config.DateColumn("Deadline"),
        "Status": st.column_config.SelectboxColumn(options=["Not Started", "In Progress", "Completed", "On Hold"]),
        "Comments": st.column_config.TextColumn("Comments", width="large")
    }
)

# --- SAVE ---
if st.button("💾 Sync & Prepare for Save"):
    st.session_state.main_df = edited_df
    csv = edited_df.to_csv(index=False).encode('utf-8')
    st.download_button("Download Updated CSV", data=csv, file_name='tracker_data.csv')
    st.success("Synced! Download and upload to GitHub to lock in changes.")
