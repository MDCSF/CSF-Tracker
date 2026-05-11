import streamlit as st
import pandas as pd
from datetime import date

st.set_page_config(page_title="CSF Action Dashboard", layout="wide")

# --- 1. DATA LOADING & CLEANING ---
@st.cache_data
def load_data():
    try:
        # Load data and handle the CSV structure
        df = pd.read_csv('tracker_data.csv', skiprows=1)
        df.columns = df.columns.str.strip()
        
        # Remove junk columns 8 and 9 (index 7 and 8)
        cols_to_keep = [c for i, c in enumerate(df.columns) if i not in [7, 8]]
        df = df[cols_to_keep]

        # Force Progress to be numeric (handling 1 vs 0.75 vs 75%)
        df['Progress %'] = pd.to_numeric(df['Progress %'], errors='coerce').fillna(0.0)
        if df['Progress %'].max() > 1.0:
            df['Progress %'] = df['Progress %'] / 100.0
            
        # Clean Deadlines
        df['Deadline'] = pd.to_datetime(df['Deadline'], errors='coerce').dt.date
        
        return df
    except Exception as e:
        st.error(f"Error loading tracker: {e}")
        return None

if 'main_df' not in st.session_state:
    st.session_state.main_df = load_data()

df = st.session_state.main_df

# --- 2. HEALTH & ALERT LOGIC ---
def get_health(row):
    today = date.today()
    deadline = row['Deadline']
    progress = row['Progress %']
    if str(row['Status']).strip() == 'Completed' or progress >= 1.0: return "🟢 Done"
    if pd.notnull(deadline) and deadline < today: return "🔴 OVERDUE"
    if pd.notnull(deadline) and (deadline - today).days <= 7: return "🟡 AT RISK"
    return "⚪ Pending"

df['Health'] = df.apply(get_health, axis=1)

# --- 3. THE VISUAL DASHBOARD ---
st.title("🚀 CSF Action Dashboard")

c1, c2, c3, c4 = st.columns(4)
overdue_df = df[df['Health'] == "🔴 OVERDUE"]
at_risk_df = df[df['Health'] == "🟡 AT RISK"]

c1.metric("Total Items", len(df))
c2.metric("🔴 Overdue", len(overdue_df))
c3.metric("🟡 At Risk", len(at_risk_df))
c4.metric("Avg. Progress", f"{int(df['Progress %'].mean() * 100)}%")

st.divider()

col_left, col_right = st.columns(2)

with col_left:
    st.subheader("📊 Task Status Distribution")
    st.bar_chart(df['Status'].value_counts())

with col_right:
    st.subheader("⚠️ Red Alert: Who is Late?")
    if len(overdue_df) > 0:
        # Grouping by owner to see who owns the late items
        late_stats = overdue_df.groupby('Owner').size()
        st.bar_chart(late_stats)
    else:
        st.success("High Performance! No overdue items found. ✅")

# --- 4. THE LIVE TRACKER ---
st.subheader("📝 Master Action Tracker")
owners = sorted(df['Owner'].dropna().unique().tolist())
selected_owner = st.sidebar.multiselect("Filter by Team Member", options=owners, default=owners)
filtered_df = df[df['Owner'].isin(selected_owner)]

edited_df = st.data_editor(
    filtered_df,
    num_rows="dynamic",
    use_container_width=True,
    hide_index=True,
    column_config={
        "Health": st.column_config.TextColumn("Health", width="small"),
        "Progress %": st.column_config.NumberColumn("Progress (%)", format="%.2f", min_value=0, max_value=1),
        "Deadline": st.column_config.DateColumn("Deadline"),
        "Status": st.column_config.SelectboxColumn(options=["Not Started", "In Progress", "Completed", "On Hold"]),
        "Priority": st.column_config.SelectboxColumn(options=["Low", "Medium", "High"]),
        "Comments": st.column_config.TextColumn("Comments", width="large")
    }
)

# --- 5. SYNC & SAVE ---
if st.button("💾 Sync Dashboard & Download"):
    st.session_state.main_df = edited_df
    csv = edited_df.to_csv(index=False).encode('utf-8')
    st.download_button("Download CSV for GitHub", data=csv, file_name='tracker_data.csv')
    st.success("Dashboard updated! Download and upload to GitHub to save permanently.")
